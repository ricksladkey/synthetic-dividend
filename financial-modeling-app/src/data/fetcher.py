import os
import pickle
from datetime import datetime, timedelta
import pandas as pd

try:
    import yfinance as yf
except Exception:
    yf = None


class HistoryFetcher:
    """Simple per-ticker cache. Cache file stores a pandas DataFrame (history) for the ticker.
    When asked for a range, it reuses cached rows if they cover the request; otherwise it
    downloads missing ranges and updates the cache file.
    """

    def __init__(self, cache_dir=None):
        if cache_dir is None:
            cache_dir = os.path.join(os.path.dirname(__file__), "..", "cache")
        self.cache_dir = os.path.abspath(cache_dir)
        os.makedirs(self.cache_dir, exist_ok=True)

    def _cache_path(self, ticker):
        return os.path.join(self.cache_dir, f"{ticker.upper()}.pkl")

    def _load_cache(self, ticker):
        path = self._cache_path(ticker)
        if os.path.exists(path):
            try:
                with open(path, "rb") as f:
                    df = pickle.load(f)
                return df
            except Exception:
                return None
        return None

    def _save_cache(self, ticker, df):
        path = self._cache_path(ticker)
        try:
            with open(path, "wb") as f:
                pickle.dump(df, f)
        except Exception:
            pass

    def _download(self, ticker, start, end):
        if yf is None:
            raise RuntimeError("yfinance not installed or failed to import")
        # yfinance uses inclusive start, exclusive end for the 'end' param; add a day buffer
        start_dt = datetime.combine(start, datetime.min.time()) - timedelta(days=1)
        end_dt = datetime.combine(end, datetime.min.time()) + timedelta(days=1)
        df = yf.download(ticker, start=start_dt.strftime("%Y-%m-%d"), end=end_dt.strftime("%Y-%m-%d"), progress=False)
        if df is None or df.empty:
            return pd.DataFrame()
        df = df[["Close"]].dropna()
        return df

    def get_history(self, ticker, start_date, end_date):
        ticker = ticker.upper()
        cached = self._load_cache(ticker)
        if cached is None or cached.empty:
            df_new = self._download(ticker, start_date, end_date)
            if df_new.empty:
                return pd.DataFrame()
            self._save_cache(ticker, df_new)
            mask = (pd.to_datetime(df_new.index).date >= start_date) & (pd.to_datetime(df_new.index).date <= end_date)
            return df_new.loc[mask].copy()

        # have cache: check coverage
        cached_dates = pd.to_datetime(cached.index).date
        cache_min = min(cached_dates)
        cache_max = max(cached_dates)

        need_download = False
        updated = cached.copy()

        if start_date < cache_min:
            df_left = self._download(ticker, start_date, cache_min - timedelta(days=1))
            if not df_left.empty:
                updated = pd.concat([df_left, updated]).sort_index()
                need_download = True

        if end_date > cache_max:
            df_right = self._download(ticker, cache_max + timedelta(days=1), end_date)
            if not df_right.empty:
                updated = pd.concat([updated, df_right]).sort_index()
                need_download = True

        if need_download:
            updated = updated[~updated.index.duplicated(keep="first")]
            self._save_cache(ticker, updated)

        mask = (pd.to_datetime(updated.index).date >= start_date) & (pd.to_datetime(updated.index).date <= end_date)
        return updated.loc[mask].copy()
