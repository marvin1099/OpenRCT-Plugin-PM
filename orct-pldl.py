#!/usr/bin/env python3
import os
import sys
import time
import json
import select
import argparse
import requests
import datetime
import urllib.request
import zipfile

class PluginDatabaseSchema: # Constructs Plugin (List) URL requests
    def __init__(self):
        self.plugin_database_url = "https://openrct2plugins.org/"
        self.plugin_sub_list = "list/"
        self.plugin_sub_plugin = "plugin/"

        self.start_par = "?"
        self.merge_par = "&"

        self.search_req = "search="
        self.search_par = ""

        self.sort_req = "sort="
        self.sort_par = "updated"

        self.page_req = "p="
        self.page_par = 1

        self.results_req = "results="
        self.results_par = 100

        self.json_par = "json"

        self.plugin_id = ""

    def _build_request_url(self) -> str:
        query_parts = []

        if self.sort_par:
            query_parts.append(self.sort_req + str(self.sort_par))

        if self.search_par:
            query_parts.append(self.search_req + str(self.search_par))

        if self.page_par:
            query_parts.append(self.page_req + str(self.page_par))

        if self.results_par:
            query_parts.append(self.results_req + str(self.results_par))

        if self.json_par:
            query_parts.append(self.json_par)

        full_query = str(self.start_par + self.merge_par.join(query_parts)) if query_parts else ""

        return self.plugin_database_url + self.plugin_sub_list + full_query

    def search_set_querys(
        self,
        search_par=None,
        sort_par=None,
        page_par=None,
        results_par=None
    ) -> None:
        search_par = search_par or self.search_par
        sort_par = sort_par or self.sort_par
        page_par = page_par or self.page_par
        results_par = results_par or self.results_par

        self.search_par = search_par
        self.sort_par = sort_par
        self.page_par = page_par
        self.results_par = results_par

    def search_with_querys(
        self,
        search_par=None,
        sort_par=None,
        page_par=None,
        results_par=None
    ) -> str:
        search_par = search_par or self.search_par
        sort_par = sort_par or self.sort_par
        page_par = page_par or self.page_par
        results_par = results_par or self.results_par

        self.search_set_querys(search_par, sort_par, page_par, results_par)
        return self._build_request_url()

    def page_query(
        self,
        page_par = None,
    ) -> str:
        page_par = page_par or self.page_par
        self.search_set_querys(page_par = page_par)
        return self._build_request_url()

    @property
    def search_url(self) -> str:
        return self._build_request_url()

    def plugin_request_url(self, plugin_id = None) -> str:
        plugin_id = plugin_id or self.plugin_id
        return self.plugin_database_url + self.plugin_sub_plugin + str(plugin_id) + self.start_par + self.json_par

    @property
    def plugin_url(self) -> str:
        return self.plugin_request_url()

class RequestCachedURL: # Cache URL requests
    def __init__(self, cache_file: str = "url_cache.json"):
        self.cache_file = cache_file
        self.cache: dict = {}
        self.max_retries = 5
        self.wait_between_retries = 10
        self._load_cache()

    def _load_cache(self) -> None:
        """Load cache from disk if it exists."""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    self.cache = json.load(f)
            except (json.JSONDecodeError, OSError):
                print("[WARNING] Cache file is corrupt or unreadable, starting fresh.")
                self.cache = {}
        else:
            self.cache = {}

    def _save_cache(self) -> None:
        """Persist the current cache to disk."""
        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self.cache, f, indent=2)
        except OSError as e:
            print(f"[ERROR] Failed to write cache file: {e}")

    def _is_stale(self, key: str) -> bool:
        """Determine whether the cached entry is stale or missing."""
        entry = self.cache.get(key)
        if not entry:
            return True
        pulled_last = entry.get("pulled_last", 0)
        refresh_secs = entry.get("refresh_secs", 3600)
        now = time.time()
        return (now - pulled_last) > refresh_secs or (now - pulled_last) < 0

    def get_json(self, url: str, refresh_secs: int = 3600) -> dict:
        self._load_cache()  # Re-read cache before checking
        if self._is_stale(url):
            #print(f"[FETCH] {url}")
            for attempt in range(self.max_retries):
                try:
                    with urllib.request.urlopen(url) as response:
                        if response.status != 200:
                            raise Exception(f"Failed to fetch URL: {url} (status {response.status})")
                        data = json.loads(response.read())
                        self.cache[url] = {
                            "pulled_last": int(time.time()),
                            "refresh_secs": refresh_secs,
                            "data": data,
                        }
                        self._save_cache()
                        break
                except (urllib.error.URLError, Exception) as e:
                    print(f"[RETRY {attempt+1}/{self.max_retries}] Error fetching {url}: {e}")
                    if attempt < self.max_retries - 1:
                        time.sleep(self.wait_between_retries)
                    else:
                        raise
        else:
            #print(f"[CACHED] {url}")
            pass

        return self.cache[url]["data"]


    def download_file(self, url: str, path: str) -> None:
        for attempt in range(self.max_retries):
            try:
                print(f"[DOWNLOAD] {url} -> {path}")
                with urllib.request.urlopen(url) as response, open(path, "wb") as out_file:
                    if response.status != 200:
                        raise Exception(f"Failed to download {url}: status {response.status}")
                    out_file.write(response.read())
                return
            except (urllib.error.URLError, Exception) as e:
                print(f"[RETRY {attempt+1}/{self.max_retries}] Error downloading {url}: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.wait_between_retries)
                else:
                    raise

class PluginDownloader:
    def __init__(self):
        # Initialize URLs, caches, and helper classes
        pass

    def fetch_plugin_details(self, plugin_id: str):
        # Retrieve extended metadata for a specific plugin
        pass

    def should_ignore(self, plugin_name: str) -> bool:
        # Check against the ignore list
        pass

    def get_matching_files(self, plugin_details: "PluginDetails"):
        # Apply rules to releases or repo to find relevant files
        pass

    def download_and_save_plugin(self, plugin_file: "PluginFile", save_path: str) -> None:
        # Download the JS file and store it using the correct versioning info
        pass

    def run_bulk_download(self) -> None:
        # Main download loop: iterate plugin list, filter, get files, download
        pass

class PluginIndex: # Gets and holds all plugins
    def __init__(self):
        self.schema = PluginDatabaseSchema()
        self.urlcache = RequestCachedURL()
        self._plugin_list: dict[str, dict] = {}
        self._result_list: dict[str, dict] = {}
        self._result_requested: bool = False

    def load_plugin_list(self) -> dict[str, dict]:
        self._plugin_list = {}
        first_page, pages = self._load_page(1)
        self._plugin_list.update(first_page)

        # Handle pagination
        for p in range(2, pages + 1):
            page_data, _ = self._load_page(p)
            self._plugin_list.update(page_data)

        self._result_requested = False
        return self._plugin_list

    def _load_page(self, page: int) -> tuple[dict, int]:
        self.schema.page_par = page
        page_url = self.schema.search_url
        data = self.urlcache.get_json(page_url)
        return data.get("data", {}), int(data.get("info", {}).get("pages", 1))

    def filter_plugins(
        self,
        filter_key: str = None,
        filter_value: str = None,
        sort_key: str = None,
        reverse: bool = False,
        main_dict: dict = {}
    ) -> list[tuple[str, dict]]:
        main_dict = main_dict or self.load_plugin_list()
        return self.refilter_plugins(filter_key, filter_value, sort_key, reverse, main_dict)

    def refilter_plugins(
        self,
        filter_key: str = None,
        filter_value: str = None,
        sort_key: str = None,
        reverse: bool = False,
        main_dict: dict = None
    ) -> list[tuple[str, dict]]:
        main_dict = main_dict or self._result_list if self._result_requested else self.load_plugin_list()

        self._result_list = main_dict
        self._result_requested = True

        if filter_key and filter_value:
            terms = filter_value.split()

            def match(entry: dict) -> bool:
                value = entry.get(filter_key)
                if not value:
                    return False

                if filter_key == "tags":
                    tag_list = [tag_obj.get("tag", "") for tag_obj in value]
                    return all(term in tag_list for term in terms)

                return all(term in str(value) for term in terms)

            self._result_list = {p_id: info for p_id, info in self._result_list.items() if match(info)}

        if sort_key:
            self._result_list = dict(sorted(self._result_list.items(), key=lambda item: item[1].get(sort_key), reverse=reverse))

        return self._result_list

    def filterd_plugins(self):
        return self._result_list if self._result_requested else self.load_plugin_list()

    def print_data(self) -> None:
        print(json.dumps(self._result_list if self._result_requested else self.load_plugin_list(), indent=4))

    def get_plugin_meta(self, plugin_id: str) -> dict:
        self.load_plugin_list()
        return self._plugin_list.get(plugin_id, {})

    def get_plugin_detail(self, plugin_id: str) -> dict:
        self.load_plugin_list()
        url = self.schema.plugin_request_url(plugin_id)
        return self.urlcache.get_json(url)

class PluginInfo: # Get info about a single plugin
    def __init__(self, plugin_id: str, index: PluginIndex):
        self.plugin_id = plugin_id
        self._index = index

        self._basic_info = None
        self._basic_info_loaded_for = None
        self._basic_info_found = None

        self._details = None
        self._details_loaded_for = None
        self._details_found = None

    def _load_basic_info(self):
        if not self.plugin_id or self._basic_info_loaded_for == self.plugin_id:
            return

        self._basic_info = self._index.get_plugin_meta(self.plugin_id)
        self._basic_info_loaded_for = self.plugin_id

        keys_to_check = [
            "name", "description", "submittedAt",
            "updatedAt", "thumbnail", "stargazers", "owner",
            "licenseName", "username", "avatarUrl", "tags"
        ]
        self._basic_info_found = any(self._basic_info.get(k) for k in keys_to_check)

    def _load_details(self):
        if not self.plugin_id or self._details_loaded_for == self.plugin_id:
            return

        self._load_basic_info()
        if not self._basic_info_found:
            self._details = {}
            self._details_found = False
            return

        self._details = self._index.get_plugin_detail(self.plugin_id)
        self._details_loaded_for = self.plugin_id

        keys_to_check = ["readme", "url", "licenseUrl", "ownerUrl"]
        self._details_found = any(self._details.get(k) for k in keys_to_check)

    def print_data(self):
        self._load_details()
        dic = dict(self._basic_info)
        dic.update(self._details)
        print(json.dumps(dic, indent=4))

    # Base propertys
    @property
    def basic_info_found(self) -> bool: # Any Base propertys set?
        self._load_basic_info()
        return bool(self._basic_info_found)

    @property
    def id(self) -> str:
        self._load_basic_info()
        return self._basic_info.get("id", None)

    @property
    def name(self) -> str:
        self._load_basic_info()
        return self._basic_info.get("name", None)

    @property
    def description(self) -> str:
        self._load_basic_info()
        return self._basic_info.get("description", None)

    @property
    def submittedAt(self) -> int:
        self._load_basic_info()
        return self._basic_info.get("submittedAt", None)

    @property
    def updatedAt(self) -> int:
        self._load_basic_info()
        return self._basic_info.get("updatedAt", None)

    @property
    def usesCustomOpenGraphImage(self) -> str:
        self._load_basic_info()
        return self._basic_info.get("usesCustomOpenGraphImage", None)

    @property
    def thumbnail(self) -> str:
        self._load_basic_info()
        return self._basic_info.get("thumbnail", None)

    @property
    def stargazers(self) -> int:
        self._load_basic_info()
        return self._basic_info.get("stargazers", None)

    @property
    def owner(self) -> str:
        self._load_basic_info()
        return self._basic_info.get("owner", None)

    @property
    def licenseName(self) -> str:
        self._load_basic_info()
        return self._basic_info.get("licenseName", None)

    @property
    def username(self) -> str:
        self._load_basic_info()
        return self._basic_info.get("username", None)

    @property
    def avatarUrl(self) -> str:
        self._load_basic_info()
        return self._basic_info.get("avatarUrl", None)

    @property
    def tags(self) -> dict[int, dict]:
        self._load_basic_info()
        return self._basic_info.get("tags", None)

    # Expanded propertys
    @property
    def details_found(self) -> bool: # Any Expanded propertys set?
        self._load_details()
        return bool(self._details_found)

    @property
    def readme(self) -> str:
        self._load_details()
        return self._details.get("readme", None)

    @property
    def url(self) -> str:
        self._load_details()
        return self._details.get("url", None)

    @property
    def licenseUrl(self) -> str:
        self._load_details()
        return self._details.get("licenseUrl", None)

    @property
    def ownerUrl(self) -> str:
        self._load_details()
        return self._details.get("ownerUrl", None)


class PluginRelease:
    def __init__(self, tag: str, assets):
        # Versioned release data
        pass

class PluginFile:
    def __init__(self, name: str, download_url: str, version: str):
        # Represents a JS file that can be downloaded
        pass

    def matches_rule(self, rule_patterns) -> bool:
        # Check against patterns from rules file
        pass

class RuleManager:
    def __init__(self, rules_url: str):
        # Load rules (e.g., file patterns like *.js or /dist/*.js)
        pass

    def match(self, filename: str) -> bool:
        # Check if a filename matches any rule pattern
        pass

class IgnoreList:
    def __init__(self, url: str):
        # Load ignore names from a URL
        pass

    def is_ignored(self, name: str) -> bool:
        # Check if a plugin name is ignored
        pass


if __name__ == "__main__":
    index = PluginIndex()
    #print("---")
    #index.print_data()
    #print("---")
    index.filter_plugins("name","OpenRCT2","stargazers",True)
    #index.print_data()
    print("---")
    plugins = index.filterd_plugins()
    if plugins:
        plugin_id = list(plugins)[0] # example id: MDEwOlJlcG9zaXRvcnkzNTIwNzU1OTY=
        info = PluginInfo(plugin_id, index)
        info.print_data()

