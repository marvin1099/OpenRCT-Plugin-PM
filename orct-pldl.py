#!/usr/bin/env python3
import os
import sys
import time
import json
import select
import argparse
import datetime
import urllib.request
import zipfile


class PluginDatabaseSchema:
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

    def search_set_querys(self, search_par=None, sort_par=None, page_par=None, results_par=None) -> None:
        search_par = search_par or self.search_par
        sort_par = sort_par or self.sort_par
        page_par = page_par or self.page_par
        results_par = results_par or self.results_par

        self.search_par = search_par
        self.sort_par = sort_par
        self.page_par = page_par
        self.results_par = results_par

    def search_with_querys(self, search_par=None, sort_par=None, page_par=None, results_par=None) -> str:
        search_par = search_par or self.search_par
        sort_par = sort_par or self.sort_par
        page_par = page_par or self.page_par
        results_par = results_par or self.results_par

        self.search_set_querys(search_par, sort_par, page_par, results_par)
        return self._build_request_url()

    def page_query(self, page_par=None) -> str:
        page_par = page_par or self.page_par
        self.search_set_querys(page_par=page_par)
        return self._build_request_url()

    @property
    def search_url(self) -> str:
        return self._build_request_url()

    def plugin_request_url(self, plugin_id=None) -> str:
        plugin_id = plugin_id or self.plugin_id
        return self.plugin_database_url + self.plugin_sub_plugin + str(plugin_id) + self.start_par + self.json_par

    @property
    def plugin_url(self) -> str:
        return self.plugin_request_url()


class RequestCachedURL:
    def __init__(self, cache_file: str = "url_cache.json"):
        self.cache_file = cache_file
        self.cache: dict = {}
        self.max_retries = 5
        self.wait_between_retries = 10
        self._load_cache()

    def _load_cache(self) -> None:
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
        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self.cache, f, indent=2)
        except OSError as e:
            print(f"[ERROR] Failed to write cache file: {e}")

    def _is_stale(self, key: str) -> bool:
        entry = self.cache.get(key)
        if not entry:
            return True
        pulled_last = entry.get("pulled_last", 0)
        refresh_secs = entry.get("refresh_secs", 3600)
        now = time.time()
        return (now - pulled_last) > refresh_secs or (now - pulled_last) < 0

    def get_json(self, url: str, refresh_secs: int = 3600) -> dict:
        self._load_cache()
        if self._is_stale(url):
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
                except Exception as e:
                    print(f"[RETRY {attempt+1}/{self.max_retries}] Error fetching {url}: {e}")
                    if attempt < self.max_retries - 1:
                        time.sleep(self.wait_between_retries)
                    else:
                        raise
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
            except Exception as e:
                print(f"[RETRY {attempt+1}/{self.max_retries}] Error downloading {url}: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.wait_between_retries)
                else:
                    raise


class PluginIndex:
    def __init__(self, cache_file: str = "url_cache.json"):
        self.schema = PluginDatabaseSchema()
        self.urlcache = RequestCachedURL(cache_file)
        self._plugin_list: dict = {}
        self._result_list: dict = {}
        self._result_requested: bool = False

    def load_plugin_list(self) -> dict:
        self._plugin_list = {}
        first_page, pages = self._load_page(1)
        self._plugin_list.update(first_page)

        for p in range(2, pages + 1):
            page_data, _ = self._load_page(p)
            self._plugin_list.update(page_data)

        self._result_requested = False
        return self._plugin_list

    def _load_page(self, page: int) -> tuple:
        self.schema.page_par = page
        page_url = self.schema.search_url
        data = self.urlcache.get_json(page_url)
        return data.get("data", {}), int(data.get("info", {}).get("pages", 1))

    def filter_plugins(self, filter_key: str = None, filter_value: str = None, sort_key: str = None, reverse: bool = False, main_dict: dict = None) -> dict:
        main_dict = main_dict or self.load_plugin_list()
        return self.refilter_plugins(filter_key, filter_value, sort_key, reverse, main_dict)

    def refilter_plugins(self, filter_key: str = None, filter_value: str = None, sort_key: str = None, reverse: bool = False, main_dict: dict = None) -> dict:
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

    def get_plugin_meta(self, plugin_id: str) -> dict:
        self.load_plugin_list()
        return self._plugin_list.get(plugin_id, {})

    def get_plugin_detail(self, plugin_id: str) -> dict:
        self.load_plugin_list()
        url = self.schema.plugin_request_url(plugin_id)
        return self.urlcache.get_json(url)


class OpenRCTPluginDownloader:
    def __init__(self, config):
        self.storefile = config
        self.github = "https://github.com"
        self.repo_api_base = "https://api.github.com/repos"
        self.scanurl = "git/trees/master?recursive=1"
        self.plugin_ignore_url = "https://codeberg.org/marvin1099/OpenRCT-Plugin-PM/raw/branch/main/ignore.json"
        self.instant_timeout = False
        self.plugin_ignore_list = []
        self.dignore = False
        self.online_plugins = []
        self.local_plugins = []
        self.last_config_sync = 0
        self.last_update = 0
        self.update_config_interval = 60*60
        self.update_plugins_interval = 60*60*24
        self.plugin_index = PluginIndex()

    def load_data(self):
        if os.path.isfile(self.storefile):
            with open(self.storefile, 'r') as file:
                data = json.load(file)
                self.online_plugins = data.get("online_plugins", [])
                self.local_plugins = data.get("local_plugins", [])
                self.plugin_ignore_url = data.get("plugin_ignore_url", self.plugin_ignore_url)
                self.plugin_ignore_list = data.get("plugin_ignore_list", [])
                self.last_config_sync = data.get("last_config_sync", 0)
                self.last_update = data.get("last_plugin_update", 0)
                self.update_config_interval = data.get("config_sync_interval", 60*60)
                self.update_plugins_interval = data.get("plugin_update_interval", 60*60*24)

    def save_data(self):
        data = {
            "online_plugins": self.online_plugins,
            "local_plugins": self.local_plugins,
            "plugin_ignore_url": self.plugin_ignore_url,
            "plugin_ignore_list": self.plugin_ignore_list,
            "last_config_sync": self.last_config_sync,
            "last_plugin_update": self.last_update,
            "config_sync_interval": self.update_config_interval,
            "plugin_update_interval": self.update_plugins_interval
        }
        with open(self.storefile, 'w') as file:
            json.dump(data, file, indent=4)

    def update_plugins(self, skipcurrent=True):
        print("Updating plugins")
        for local_plugin in self.local_plugins:
            online_plugin = self.is_plugin_available(local_plugin['name'])
            if online_plugin:
                combined_info = {
                    "name": local_plugin['name'],
                    "download_time": int(time.time()),
                    "last_updated": online_plugin.get('last_updated', 0),
                    "files": []
                }
                index = self.get_plugin_index_by_name(local_plugin['name'])
                self.local_plugins[index] = combined_info
                self.github_download(online_plugin, skipcurrent)
                print("")
            else:
                print(f"Plugin '{local_plugin['name']}' not found online.")
            self.last_update = int(time.time())

    def generate_repo_api_url(self, plugin):
        author = plugin.get('author', '')
        name = plugin.get('name', '')
        
        if 'github_url' in plugin:
            gh_url = plugin['github_url']
            if gh_url and 'github.com' in gh_url:
                parts = gh_url.replace('https://github.com/', '').split('/')
                if len(parts) >= 2:
                    return f"{self.repo_api_base}/{parts[0]}/{parts[1]}"
        
        return f"{self.repo_api_base}/{author}/{name}"

    def load_ignore_list(self):
        try:
            with urllib.request.urlopen(self.plugin_ignore_url) as response:
                ignore_list_data = json.loads(response.read())
                updated_ignore_list = list(set(self.plugin_ignore_list + ignore_list_data))
                self.plugin_ignore_list = updated_ignore_list
                return updated_ignore_list
        except Exception as e:
            print(f"Error loading plugin ignore list: {e}")
            return self.plugin_ignore_list

    def update_index(self):
        print("Updating index")
        plugin_list = []
        try:
            plugins_dict = self.plugin_index.load_plugin_list()
            for plugin_id, plugin_data in plugins_dict.items():
                tags_list = []
                if 'tags' in plugin_data and plugin_data['tags']:
                    for tag_obj in plugin_data['tags']:
                        if isinstance(tag_obj, dict):
                            tags_list.append(tag_obj.get('tag', ''))
                        else:
                            tags_list.append(str(tag_obj))

                plugin_info = {
                    'name': plugin_data.get('name', ''),
                    'description': plugin_data.get('description', ''),
                    'author': plugin_data.get('username', ''),
                    'stars': plugin_data.get('stargazers', 0),
                    'submitted': plugin_data.get('submittedAt', 0),
                    'last_updated': plugin_data.get('updatedAt', 0),
                    'license': plugin_data.get('licenseName', 'N/A'),
                    'url_identifier': plugin_id,
                    'tags': tags_list
                }
                plugin_list.append(plugin_info)
            print(f"Loaded {len(plugin_list)} plugins from API")
        except Exception as e:
            print(f"Error updating index: {e}")
            plugin_list = []

        self.online_plugins = plugin_list
        self.last_config_sync = int(time.time())

    def print_results(self, results):
        print("-" * 50)
        for plugin in reversed(results):
            print(f"Name: {plugin.get('name', 'N/A')}")
            print(f"Description: {plugin.get('description', 'N/A')}")
            print(f"Author: {plugin.get('author', 'N/A')}")
            print(f"Stars: {plugin.get('stars', 0)}")
            print(f"Submitted: {plugin.get('submitted', 0)}")
            print(f"Last Updated: {plugin.get('last_updated', 0)}")
            print(f"License: {plugin.get('license', 'N/A')}")
            print(f"URL Identifier: {plugin.get('url_identifier', 'N/A')}")
            if plugin.get('name') in self.plugin_ignore_list:
                print("In Ignore List: True")
            if plugin.get('tags'):
                print(f"Tags: {', '.join(plugin['tags'])}")
            print("-" * 50)

    def sort_plugins_by_key(self, search_results, keys=[None]):
        rev = False
        sort_key = False
        for found_key in keys:
            if found_key in ['n', 's', 'm', 'l', None]:
                sort_key = found_key
            if found_key == "r":
                rev = True
        if sort_key == False:
            print("Invalid sort key. Supported keys are: None, 'n' for name, 's' for stars, 'm' for submitted, 'l' for last_updated, 'r' for reverse results.")
            return search_results
        elif sort_key == None:
            return search_results

        sorted_results = []
        if sort_key == 'n':
            sorted_results = sorted(search_results, key=lambda x: x.get('name', ''), reverse=rev)
        elif sort_key == 's':
            sorted_results = sorted(search_results, key=lambda x: x.get('stars', 0), reverse=not rev)
        elif sort_key == 'm':
            sorted_results = sorted(search_results, key=lambda x: x.get('submitted', 0), reverse=rev)
        elif sort_key == 'l':
            sorted_results = sorted(search_results, key=lambda x: x.get('last_updated', 0), reverse=rev)

        return sorted_results

    def search_plugins(self, query, fields=None, number=0):
        if not fields:
            fields = ["n"]
        if number == None:
            number = 0
        if "x" not in fields:
            unumber = int(time.time()) - int(number)
        else:
            unumber = int(number)

        search_results = []

        for plugin in self.online_plugins:
            matched = False
            intmatch = False
            strict = False
            if "r" in fields:
                strict = True
            else:
                strict = False
            for field in fields:
                if "g" in fields and str(number).isdigit():
                    if (field == "s" and int(number) < plugin.get("stars", 0)) or \
                        (field == "m" and int(unumber) < plugin.get("submitted", 0)) or \
                        (field == "u" and int(unumber) < plugin.get("last_updated", 0)):
                        intmatch = True
                elif "b" in fields and str(number).isdigit():
                    if (field == "s" and int(number) > plugin.get("stars", 0)) or \
                        (field == "m" and int(unumber) > plugin.get("submitted", 0)) or \
                        (field == "u" and int(unumber) > plugin.get("last_updated", 0)):
                        intmatch = True

                plugin_name = plugin.get('name', '') or ''
                plugin_desc = plugin.get('description', '') or ''
                plugin_author = plugin.get('author', '') or ''
                plugin_license = plugin.get('license', '') or ''
                plugin_url_id = plugin.get('url_identifier', '') or ''
                plugin_tags = plugin.get('tags', []) or []

                if field == "n" and query.lower() in plugin_name.lower():
                    matched = True
                elif field == "d" and plugin_desc and query.lower() in plugin_desc.lower():
                    matched = True
                elif field == "a" and plugin_author and query.lower() in plugin_author.lower():
                    matched = True
                elif field == "s" and str(number).isdigit() and int(number) == plugin.get("stars", 0):
                    intmatch = True
                elif field == "m" and str(number).isdigit() and int(number) == plugin.get("submitted", 0):
                    intmatch = True
                elif field == "u" and str(number).isdigit() and int(number) == plugin.get("last_updated", 0):
                    intmatch = True
                elif field == "l" and query.lower() in plugin_license.lower():
                    matched = True
                elif field == "i" and query.lower() in plugin_url_id.lower():
                    matched = True
                elif field == "t" and any(tag.lower() == query.lower() for tag in plugin_tags):
                    if "p" in fields:
                        if any(query.lower() in tag.lower() for tag in plugin_tags):
                            matched = True
                    else:
                        if any(tag.lower() == query.lower() for tag in plugin_tags):
                            matched = True

                if matched and intmatch and strict:
                    search_results.append(plugin)
                    break
                elif (matched or intmatch) and not strict:
                    search_results.append(plugin)
                    break
        return search_results

    def input_with_timeout(self, prompt, timeout=5):
        if self.instant_timeout:
            return None
        print(f"Timeout in {timeout} seconds\n{prompt}", end='', flush=True)
        ready, _, _ = select.select([sys.stdin], [], [], timeout)
        if ready:
            return sys.stdin.readline().strip()
        else:
            return None

    def scan_repository_for_files(self, repo_api_url, file_extension):
        files = []
        try:
            tree_url = f"{repo_api_url}/{self.scanurl}"
            with urllib.request.urlopen(tree_url) as response:
                tree_data = json.loads(response.read())

            if 'tree' in tree_data:
                for item in tree_data['tree']:
                    if item['type'] == 'blob' and item['path'].endswith(file_extension):
                        file_info = {
                            'path': item['path'],
                            'url': item['url'],
                            'release': False
                        }
                        files.append(file_info)
        except Exception as e:
            print(f"Error scanning repository: {e}")
        return files

    def sort_by_subfolder_depth(self, file_info):
        return file_info['path'].count('/')

    def what_about_plugin(self, plugin_name):
        local_plugin = next((p for p in self.local_plugins if p['name'] == plugin_name), None)
        online_plugin = next((p for p in self.online_plugins if p['name'] == plugin_name), None)

        if not local_plugin and not online_plugin:
            return "Missing"

        if not local_plugin:
            return "Uninstalled"

        if not online_plugin:
            return "Offline"

        local_last_updated = local_plugin['last_updated']
        online_last_updated = online_plugin.get('last_updated', 0)

        if local_last_updated > online_last_updated:
            return "Overdated"
        elif local_last_updated == online_last_updated:
            return "Current"
        else:
            return "Outdated"

    def is_plugin_installed(self, plugin_name):
        for plugin in self.local_plugins:
            if plugin['name'] == plugin_name:
                return plugin
        return None

    def match_installed_files_to_repo(self, installed_plugin, all_files):
        matched_files = []
        unmatched_files = []
        
        for installed_file in installed_plugin.get('files', []):
            installed_path = installed_file.get('path', '')
            installed_clean = self.strip_version_strings(os.path.basename(installed_path))
            installed_release = installed_file.get('release', False)
            
            matched = False
            for repo_file in all_files:
                repo_path = repo_file.get('path', '')
                repo_clean = self.strip_version_strings(os.path.basename(repo_path))
                repo_release = repo_file.get('release', False)
                
                if installed_clean == repo_clean and installed_release == repo_release:
                    matched_files.append(repo_file)
                    matched = True
                    break
            if not matched:
                unmatched_files.append(installed_file)

        all_files_matched = len(unmatched_files) == 0
        return matched_files, all_files_matched, unmatched_files

    def get_plugin_index_by_name(self, plugin_name):
        for index, plugin in enumerate(self.local_plugins):
            if plugin['name'] == plugin_name:
                return index
        return None

    def remove_pl_files(self, files_to_remove):
        for file_to_remove in files_to_remove:
            clean_name = file_to_remove.get("clean_name")
            if clean_name:
                path_to_remove = clean_name
            else:
                path_to_remove = os.path.basename(file_to_remove.get("path", ""))
            
            try:
                os.remove(path_to_remove)
            except:
                print(f"File not found: {path_to_remove}")
            else:
                print(f"Removed file: {path_to_remove}")

    def strip_version_strings(self, filename):
        import re
        name_without_ext = os.path.splitext(filename)[0]
        ext = os.path.splitext(filename)[1]
        
        version_patterns = [
            r'[-_]v?\d+\.\d+\.\d+',
            r'[-_]v?\d+\.\d+',
            r'[-_]v?\d+',
            r'[-_]\d{4}-\d{2}-\d{2}',
            r'[-_]\d{8,}',
            r'[-_](alpha|beta|rc)\d*',
            r'[-_]min$',
        ]
        
        for pattern in version_patterns:
            name_without_ext = re.sub(pattern, '', name_without_ext, flags=re.IGNORECASE)
        
        name_without_ext = re.sub(r'[-_]+', '_', name_without_ext)
        name_without_ext = name_without_ext.strip('_-')
        
        return name_without_ext + ext

    def download_files(self, selected_files):
        downloaded_files = []
        for file_info in selected_files:
            try:
                file_url = file_info.get('url')
                original_filename = os.path.basename(file_info.get('path', 'download.js'))
                clean_filename = self.strip_version_strings(original_filename)
                
                with urllib.request.urlopen(file_url) as response:
                    if response.status != 200:
                        raise Exception(f"Failed to download: {file_info.get('path')} (status {response.status})")
                    with open(clean_filename, 'wb') as file:
                        file.write(response.read())
                downloaded_files.append({
                    "path": file_info['path'], 
                    "release": file_info['release'],
                    "clean_name": clean_filename
                })
                print(f"Downloaded: {clean_filename}")
            except Exception as e:
                print(f"Failed to download: {file_info.get('path')} - {e}")
        return downloaded_files

    def fetch_repository_details(self, repo_api_url):
        try:
            with urllib.request.urlopen(repo_api_url) as response:
                return json.loads(response.read())
        except Exception as e:
            print(f"Error fetching repository details: {e}")
            return None

    def fetch_release_files(self, releases_url):
        try:
            with urllib.request.urlopen(releases_url) as response:
                release_data = json.loads(response.read())
                if isinstance(release_data, list) and len(release_data) > 0:
                    assets = release_data[0].get('assets', [])
                    return [{'path': asset['name'], 'url': asset['browser_download_url'], 'release': True} for asset in assets if asset['name'].endswith('.js')]
        except Exception as e:
            print(f"Error fetching release files: {e}")
        return []

    def github_download(self, plugin, skipcurrent=False):
        url_identifier = plugin.get('url_identifier', '')
        
        if url_identifier:
            try:
                detail_url = self.plugin_index.schema.plugin_request_url(url_identifier)
                plugin_details = self.plugin_index.urlcache.get_json(detail_url)
                if plugin_details and 'url' in plugin_details:
                    plugin['github_url'] = plugin_details['url']
            except Exception as e:
                print(f"Could not fetch plugin details: {e}")
        
        repo_api_url = self.generate_repo_api_url(plugin)
        repo_data = self.fetch_repository_details(repo_api_url)
        
        if not repo_data:
            print("Failed to fetch repository details")
            return
            
        last_update_time = repo_data.get('updated_at', '')
        state_select = None

        state = self.what_about_plugin(plugin.get('name', ''))
        if state == "Current" or state == "Overdated":
            if not skipcurrent:
                state_select = self.input_with_timeout("Version is already up to date\n0. To skip install\n1. To reinstall the current file setup\n2. To reinstall with a other file setup\nYour choice: ", 20)
            else:
                print(f"Skipped {plugin.get('name')} because it was up to date")
            if not state_select or state_select == "0":
                return
            if state_select != "1":
                state_select = "2"

        downloaded_plugin = {
            "name": plugin.get('name', ''),
            "download_time": int(time.time()),
            "last_updated": int(datetime.datetime.strptime(last_update_time, "%Y-%m-%dT%H:%M:%SZ").timestamp()) if last_update_time else int(time.time()),
            "files": []
        }

        print("")
        if 'releases_url' in repo_data:
            release_files = self.fetch_release_files(repo_data['releases_url'].replace('{/id}', ''))
        else:
            release_files = []

        files = self.scan_repository_for_files(repo_api_url, '.js')
        sorted_files = sorted(files, key=self.sort_by_subfolder_depth)

        all_files = release_files + sorted_files
        if state_select != "1":
            print(f"Found {len(release_files)} .js files in the latest release.")
            print(f"Found {len(files)} .js files in the repository.")
            print("")
            for index, file_info in enumerate(all_files, start=1):
                print(f"{index}. Path: {file_info['path']}, Release: {file_info['release']}")
            print("")

        selected_files = []
        if state_select:
            iplugin = self.is_plugin_installed(plugin.get('name', ''))
        if state_select == "1" and iplugin:
            selected_files, all_matched, unmatched = self.match_installed_files_to_repo(iplugin, all_files)
            if not all_matched:
                stayon = self.input_with_timeout("Not all files were matched, if you continue the following files will be removed\n" + '\n '.join([str(u) for u in unmatched]) + "\n0. skip\n1. continue anyway\nYour choice: ", 20)
                if not stayon or stayon == "0":
                    return
                self.remove_pl_files(unmatched)
        else:
            selections = self.input_with_timeout("Enter the numbers of the files to download (comma-separated), or '0' to abort: ", 40)
            print("")
            if not selections:
                selections = "1"
            if selections and selections[0] != '0':
                try:
                    selected_indices = selections.split(',')
                    selected_files = [all_files[int(index)-1] for index in selected_indices if 1 <= int(index) <= len(all_files)]
                except (ValueError, IndexError):
                    print("Invalid selection")

        if selected_files:
            downloaded_plugin["files"] = self.download_files(selected_files)
        if downloaded_plugin.get("files"):
            if state_select:
                idx = self.get_plugin_index_by_name(plugin.get('name', ''))
                if idx is not None:
                    self.local_plugins[idx] = downloaded_plugin
            else:
                self.local_plugins.append(downloaded_plugin)
        else:
            if state_select and iplugin:
                self.remove_pl_files(iplugin.get("files", []))
                idx = self.get_plugin_index_by_name(plugin.get('name', ''))
                if idx is not None:
                    self.local_plugins.pop(idx)
            print(f"No Files selected, Skipping install")

    def is_plugin_available(self, plugin_name):
        for plugin in self.online_plugins:
            if plugin.get('name') == plugin_name:
                return plugin
        return None

    def install_plugin(self, plugin_name):
        try:
            if plugin_name in self.plugin_ignore_list and not self.dignore:
                print(f"Plugin '{plugin_name}' is in the ignore list. looking for close matches")
                found_plugin = False
            else:
                found_plugin = self.is_plugin_available(plugin_name)
            if not found_plugin:
                if found_plugin == None:
                    print(f"Plugin '{plugin_name}' not found. Searching for similar plugins")
                search_results = self.search_plugins(plugin_name)

                if not self.dignore:
                    print("Checking for plugin results from ignore list and removing them")
                    search_results = [result for result in search_results if result.get('name') not in self.plugin_ignore_list]

                if not search_results:
                    print(f"No similar plugins found for '{plugin_name}'. Installation aborted.")
                    return

                print(f"Similar plugins found:")
                for idx, result in enumerate(search_results, start=1):
                    print(f"{idx}. {result.get('name', 'N/A')}")
                print("")

                selection = self.input_with_timeout("Enter the number of the plugin to install, or '0' to abort: ", 20)
                print("")
                if selection == None or selection == '0' or selection == '':
                    print("Installation aborted.")
                    return

                try:
                    selected_index = int(selection) - 1
                    selected_plugin = search_results[selected_index]
                    print(f"Installing plugin: {selected_plugin.get('name', '')}")
                    self.github_download(selected_plugin)
                    print("")
                except (ValueError, IndexError):
                    print("Invalid selection. Installation aborted.")
            else:
                print(f"Installing plugin: {plugin_name}")
                self.github_download(found_plugin)
                print("")
        except Exception as e:
            print(f"Error installing plugin: {e}")

    def remove_plugin(self, plugin_name):
        state = self.what_about_plugin(plugin_name)
        if state == "Missing" or state == "Uninstalled":
            print("Plugin not installed, Skipping removal")
            return
        idxplugin = self.get_plugin_index_by_name(plugin_name)
        if idxplugin is not None:
            self.remove_pl_files(self.local_plugins[idxplugin].get('files', []))
            self.local_plugins.pop(idxplugin)

    def list_installed_plugins(self):
        print("-" * 50)
        for plugin in reversed(self.local_plugins):
            print(f"Name: {plugin.get('name', 'N/A')}")
            print(f"Last Updated: {plugin.get('last_updated', 0)}")
            print(f"Downloaded On: {plugin.get('download_time', 0)}")
            for plfile in plugin.get('files', []):
                clean_name = plfile.get('clean_name', '')
                opath, fname = os.path.split(plfile.get('path', ''))
                if clean_name:
                    fname = clean_name
                if opath:
                    print(f"  File: {fname}, Online Path: {opath}/, Release: {plfile.get('release', False)}")
                else:
                    print(f"  File: {fname}, Release: {plfile.get('release', False)}")
            print("-" * 50)

    def list_online_plugins(self):
        print("-" * 50)
        for plugin in reversed(self.online_plugins):
            print(f"Name: {plugin.get('name', 'N/A')}")
            print(f"Description: {plugin.get('description', 'N/A')}")
            print(f"Author: {plugin.get('author', 'N/A')}")
            print(f"Stars: {plugin.get('stars', 0)}")
            print(f"Submitted: {plugin.get('submitted', 0)}")
            print(f"Last Updated: {plugin.get('last_updated', 0)}")
            print(f"License: {plugin.get('license', 'N/A')}")
            print(f"URL Identifier: {plugin.get('url_identifier', 'N/A')}")
            if plugin.get('name') in self.plugin_ignore_list:
                print("In Ignore List: True")
            if plugin.get('tags'):
                print(f"Tags: {', '.join(plugin['tags'])}")
            print("-" * 50)

    def run(self, args):
        self.load_data()

        if args.timeoutnow:
            self.instant_timeout = True

        if args.idxup or int(time.time()) - int(self.last_config_sync) > int(self.update_plugins_interval):
            self.update_index()

        if args.update or int(time.time()) - int(self.last_update) > int(self.update_plugins_interval):
            self.update_plugins()

        if args.dignore:
            self.dignore = True

        if args.ignoreurl:
            self.plugin_ignore_url = args.ignoreurl

        if args.query or args.install:
            self.plugin_ignore_list = self.load_ignore_list()

        if args.query or args.number:
            for plugin in args.query:
                self.print_results(self.sort_plugins_by_key(self.search_plugins(plugin, args.fields, args.number), args.sort))

        if args.install:
            for plugin in args.install:
                self.install_plugin(plugin)

        if args.remove:
            for plugin in args.remove:
                self.remove_plugin(plugin)

        if args.ols:
            self.list_online_plugins()

        if args.ls:
            self.list_installed_plugins()

        self.save_data()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog='orct-pldl.py',
        description='A simple OpenRCT plugin finder and downloader',
        epilog='')
    parser.add_argument('-q', '--query', nargs="+", action='extend', help='search for an online database plugin')
    parser.add_argument('-n', '--number', type=int, help='search for stars, submitted and last_updated (use g or b in fields to specify max or min)')
    parser.add_argument('-f', '--fields', nargs='+', default=['n'], choices=['n','d','a','s','g','b','m','l','i','x','t','r','p'], help='fields to search (n: name (default), d: description, a: author, s: stars, g: above, b: below, x: disable unixtime - number, m: submitted, l: license, i: url_identifier, t: tags, r: only query and number, p: enable partial tag search)')
    parser.add_argument('-s', '--sort', nargs='+', default=[None], choices=['n', 's', 'm', 'l', 'r'], help='field to sort the results (n: for name, s: stars, m: submitted, l: last_updated, r: reverse results)')
    parser.add_argument('-r', '--remove', nargs="+", action='extend', help='remove installed plugin')
    parser.add_argument('-i', '--install', nargs="+", action='extend', help='install online database plugin')
    parser.add_argument('-o', '--ols', action='store_true', help='list indexed online plugins')
    parser.add_argument('-u', '--update', action='store_true', help='force update plugins (default auto update every 24 hours)')
    parser.add_argument('-x', '--idxup', action='store_true', help='force update plugin index (default auto update every hour)')
    parser.add_argument('-t', '--timeoutnow', action='store_true', help='enable instant timeout (recommended on multiple installs, will just grab the first file for all online files)')
    parser.add_argument('-l', '--ls', action='store_true', help='list installed plugins')
    parser.add_argument('-d', '--dignore', action='store_true', help='disable ignore list')
    parser.add_argument('-g', '--ignoreurl', default='', help='set ignore url')
    parser.add_argument("-c", "--config", default="orct-pldl.json", help="Config file to use (default: orct-pldl.json)")
    args = parser.parse_args()
    downloader = OpenRCTPluginDownloader(args.config)
    downloader.run(args)
