
export const url_utils = {
    generateFilterArgs(filters) {
        if (!filters) {
            return "";
        }
        let args = '?';
        for (var name in filters) {
            if (filters[name] !== null) {
                args += `&filter.${name}=${filters[name]}`
            }
        }
        return args;
    },

    elementVisibility(elementCss, show) {
        const els = document.querySelectorAll(elementCss);
        if (els && els.length > 0) {
            if (show) {
                els[0].style.visibility = 'visible';
            } else {
                els[0].style.visibility = 'hidden';
            }
        }
    }
};


export const axios_api_cache = {
    storage: null,
    is_debug: true,
    axios: null,
    CACHE_TIMEOUT_MS: 30000, // 30 seconds

    configure_axios(axios, is_debug = false) {
        this.is_debug = is_debug;
        this.axios = axios;
        this.storage = window.sessionStorage;
        this.storage.setItem("axios_cache_setup", "true");
        if (this.is_debug) {
            console.log("[Axios-Cache] Configure");
        }
    },

    get(url) {
        const cache = this;
        if (this.is_debug) {
            console.log(`[Axios-Cache] Request url=${url}`);
        }
        let value = cache.get_cached(url);
        if (value) {
            /* eslint-disable no-unused-vars */
            return new Promise((resolve, reject) => {
                if (this.is_debug) {
                    console.log(`[Axios-Cache] Serving cached value for url=${url}`);
                }
                return resolve(value);
            });
        } else {
            return new Promise((resolve, reject) => {
                let in_flight = cache.is_in_flight(url);
                if (!in_flight) {
                    cache.mark_in_flight(url);
                    cache.axios(url).then(res=>{
                        cache.save_cached(url, res);
                        resolve(res);
                    }).catch(err => {
                        cache.save_cached(url, null);
                        reject(err);
                    });
                } else {
                    if (this.is_debug) {
                        console.log(`[Axios-Cache] Bounching request url=${url}`);
                    }
                }
            });
        }
    },

    is_in_flight(url) {
        let count = this.storage.getItem("axios_in_flight."+url);
        if (!count) {
            count = 0;
        }
        if (this.is_debug) {
            if (count == 0) {
                console.log(`[Axios-Cache] Not in flight ${url}`);
            } else {
                console.log(`[Axios-Cache] Is in flight ${count} ${url}`);                
            }
        }
        return count > 0;
    },

    mark_in_flight(url) {
        let count = this.storage.getItem("axios_in_flight."+url, "0");
        if (!count) {
            count = 0;
        }
        count++;
        this.storage.setItem("axios_in_flight."+url, count);
        if (this.is_debug) {
            console.log(`[Axios-Cache] Mark in flight count=${count} url=${url}`);
        }
    },

    save_cached(url, value) {
        let count = this.storage.getItem("axios_in_flight."+url, "0");
        count--;
        if (count > 0) {
            this.storage.setItem("axios_in_flight."+url, count);
        } else {
            this.storage.removeItem("axios_in_flight."+url);
        }
        if (value) {
            this.storage.setItem("axios_cache_timestamp."+url, Date.now());
            this.storage.setItem("axios_cache."+url, JSON.stringify(value));
        }
        if (this.is_debug) {
            if (value) {
                console.log(`[Axios-Cache] Save cached count=${count} url=${url}`);
            } else {
                console.log(`[Axios-Cache] Skip failed caching attempt count=${count} url=${url}`);
            }
        }
    },

    get_cached(url) {
        let value = this.storage.getItem("axios_cache."+url);
        if (value) {
            let age_in_mseconds = Date.now() - (this.storage.getItem("axios_cache_timestamp."+url) || 0);
            if (age_in_mseconds > this.CACHE_TIMEOUT_MS) {
                value = null;
                if (this.is_debug) {
                    console.log(`[Axios-Cache] Cached value expired url=${url}`);
                }
            }
        }
        if (this.is_debug) {
            if (value) {
                console.log(`[Axios-Cache] Get cached value for ${url}`);
            } else {
                console.log(`[Axios-Cache] No cached value for ${url}`);
            }
        }
        try {
            value = JSON.parse(value);
        } catch (e) {
            console.log(`Failed to parse into JSON value for ${url}`)
        }
        return value;
    },

    clear_cache() {
        if (this.is_debug) {
            console.log(`[Axios-Cache] Clear cache`);
        }
        for(let keyName in this.storage) {
            if (keyName.startsWith("axios_cache.")) {
                let url = keyName.slice(12);
                this.storage.removeItem(keyName);
                if (this.is_debug) {
                    console.log(`[Axios-Cache] Clear Cache url=${url}`);
                }
            }
            if (keyName.startsWith("axios_in_flight.")) {
                let url = keyName.slice(16);
                let count = this.storage.getItem(keyName, "0");
                if (this.is_debug) {
                    console.log(`[Axios-Cache] Clear InFlight count=${count} url=${url}`);
                }
                this.storage.removeItem(keyName);
            }
        }
        if (this.is_debug) {
            console.log(`[Axios-Cache] Clear done.`);
        }
    },

    cache_size() {
        for(let keyName in this.storage) {
            let size = 0;
            if (keyName.startsWith("axios_cache.")) {
                size++;
            }
            return size;
        }
    },

    in_flight_size() {
        for(let keyName in this.storage) {
            let size = 0;
            if (keyName.startsWith("axios_in_flight.")) {
                size++;
            }
            return size;
        }
    },
}