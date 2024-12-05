#include <stdio.h>
#include <stdlib.h>
#include <curl/curl.h>

const char* metaURL = "http://metadata/computeMetadata/v1/instance/network-interfaces/0/access-configs/0/external-ip";
const char* ipURL = "https://api.ipify.org";

size_t write_callback(void *contents, size_t size, size_t n, void *data) {
    size_t total_size = size * n;
    fwrite(contents, size, n, (FILE *)data);
    return total_size;
}

int main(int argc, char *argv[]) {
    const char *url = argc > 1 ? argv[1] : ipURL;

    CURL *curl;
    CURLcode res;
    struct curl_slist *headers = NULL;

    curl = curl_easy_init();
    if (!curl) {
        fprintf(stderr, "failed to initialize libcurl\n");
        return EXIT_FAILURE;
    }

    headers = curl_slist_append(headers, "Metadata-Flavor: Google");

    curl_easy_setopt(curl, CURLOPT_URL, url);
    curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, write_callback);
    curl_easy_setopt(curl, CURLOPT_WRITEDATA, stdout);

    res = curl_easy_perform(curl);
    if (res != CURLE_OK) {
        fprintf(stderr, "libcurl error: %s\n", curl_easy_strerror(res));
        curl_slist_free_all(headers);
        curl_easy_cleanup(curl);
        return EXIT_FAILURE;
    }

    curl_slist_free_all(headers);
    curl_easy_cleanup(curl);

    return EXIT_SUCCESS;
}
