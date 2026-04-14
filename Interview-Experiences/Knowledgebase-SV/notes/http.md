## HTTP
- Hyper Text Transfer Protocol
- Communication between web servers and clients
- HTTP Requests / Response
- Its stateless (each request is independent)

`GET`
Retrieves data from the server

`POST`
Submit data to the server

`PUT`
Update data already on the server

`DELETE`
Deletes data from the server

```
200 - OK
201 - OK created
301 - Moved to new URL
304 - Not modified (Cached version)
400 - Bad request
401 - Unauthorized
404 - Not found
500 - Internal server error
```

### HTTP in C++ using libcurl

For `json` parsing, I have used this amazing library [nlohmann](https://github.com/nlohmann/json).

```cpp
#include <iostream>
#include <curl/curl.h>
#include "json.hpp"
#include <fstream>

using json = nlohmann::json;
```
This callback is called everytime we receive a response from the server. We pass
into it, a pointer to user string and append the response in this string.
```cpp
// Helper function to capture server responses into a string
static size_t WriteCallback(void* contents, size_t size, size_t nmemb, std::string* out) {
    size_t totalSize = size * nmemb;
    out->append((char*)contents, totalSize);
    return totalSize;
}
```
Sending a `GET` request (it takes no argument).
We have stored the response in a JSON object:
```cpp
json httpGet(const std::string& url) {
    CURL* curl;
    CURLcode res;
    std::string readBuffer;

    curl = curl_easy_init();
    if(curl) {
        curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
        curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, WriteCallback);
        curl_easy_setopt(curl, CURLOPT_WRITEDATA, &readBuffer);

        res = curl_easy_perform(curl);
        curl_easy_cleanup(curl);

        if(res != CURLE_OK) {
            std::cerr << "GET request failed: " << curl_easy_strerror(res) << std::endl;
        }
    }
    // Do this only when the response type is JSON
    return json::parse(readBuffer);
}
```

Headers are appended like this:
```cpp
struct curl_slist* headers = NULL;
headers = curl_slist_append(headers, "Content-Type: application/json");
// headers = curl_slist_append(headers, "<SOME MORE HEADER>");
curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
```

Sending a `POST` request. It takes the data we want to post as
argument in JSON format.
Inside the function, we dump this JSON object into a c-style string.
```cpp
json httpPost(const std::string& url, const json& data) {
    CURL* curl;
    CURLcode res;
    std::string readBuffer;

    curl = curl_easy_init();
    if(curl) {
        curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
        curl_easy_setopt(curl, CURLOPT_POST, 1L);

        // JSON data
        std::string jsonData = data.dump();
        curl_easy_setopt(curl, CURLOPT_POSTFIELDS, jsonData.c_str());

        struct curl_slist* headers = NULL;
        headers = curl_slist_append(headers, "Content-Type: application/json");
        curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);

        curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, WriteCallback);
        curl_easy_setopt(curl, CURLOPT_WRITEDATA, &readBuffer);

        res = curl_easy_perform(curl);
        curl_easy_cleanup(curl);

        if(res != CURLE_OK) {
            std::cerr << "POST request failed: " << curl_easy_strerror(res) << std::endl;
        }
        long response_code;
        curl_easy_getinfo(curl, CURLINFO_RESPONSE_CODE, &response_code);
        std::cout << "Got response code: " << response_code << std::endl;
    }

    return json::parse(readBuffer);
}
```

Function to send PUT request:
```cpp
json httpPut(const std::string& url, const json& data) {
    CURL* curl;
    CURLcode res;
    std::string readBuffer;

    curl = curl_easy_init();
    if(curl) {
        curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
        curl_easy_setopt(curl, CURLOPT_CUSTOMREQUEST, "PUT");

        std::string jsonData = data.dump();
        curl_easy_setopt(curl, CURLOPT_POSTFIELDS, jsonData.c_str());

        struct curl_slist* headers = NULL;
        headers = curl_slist_append(headers, "Content-Type: application/json");
        curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);

        curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, WriteCallback);
        curl_easy_setopt(curl, CURLOPT_WRITEDATA, &readBuffer);

        res = curl_easy_perform(curl);
        curl_easy_cleanup(curl);

        if(res != CURLE_OK) {
            std::cerr << "PUT request failed: " << curl_easy_strerror(res) << std::endl;
        }
    }

    return json::parse(readBuffer);
}
```

Function to send PATCH request:
```cpp
json httpPatch(const std::string& url, const json& data) {
    CURL* curl;
    CURLcode res;
    std::string readBuffer;

    curl = curl_easy_init();
    if(curl) {
        curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
        curl_easy_setopt(curl, CURLOPT_CUSTOMREQUEST, "PATCH");

        std::string jsonData = data.dump();
        curl_easy_setopt(curl, CURLOPT_POSTFIELDS, jsonData.c_str());

        struct curl_slist* headers = NULL;
        headers = curl_slist_append(headers, "Content-Type: application/json");
        curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);

        curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, WriteCallback);
        curl_easy_setopt(curl, CURLOPT_WRITEDATA, &readBuffer);

        res = curl_easy_perform(curl);
        curl_easy_cleanup(curl);

        if(res != CURLE_OK) {
            std::cerr << "PATCH request failed: " << curl_easy_strerror(res) << std::endl;
        }
    }

    return json::parse(readBuffer);
}
```
Function to send DELETE request:
```cpp
void httpDelete(const std::string& url) {
    CURL* curl;
    CURLcode res;

    curl = curl_easy_init();
    if(curl) {
        curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
        curl_easy_setopt(curl, CURLOPT_CUSTOMREQUEST, "DELETE");

        res = curl_easy_perform(curl);
        curl_easy_cleanup(curl);

        if(res != CURLE_OK) {
            std::cerr << "DELETE request failed: " << curl_easy_strerror(res) << std::endl;
        }
    }
}
```
#### Putting everything together:

```cpp
#include <iostream>
#include <curl/curl.h>
#include "json.hpp"
#include <fstream>

using json = nlohmann::json;

// Helper function to capture server responses into a string
static size_t WriteCallback(void* contents, size_t size, size_t nmemb, std::string* out) {
    size_t totalSize = size * nmemb;
    out->append((char*)contents, totalSize);
    return totalSize;
}

// Function to send GET request
json httpGet(const std::string& url) {
    CURL* curl;
    CURLcode res;
    std::string readBuffer;

    curl = curl_easy_init();
    if(curl) {
        curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
        curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, WriteCallback);
        curl_easy_setopt(curl, CURLOPT_WRITEDATA, &readBuffer);

        res = curl_easy_perform(curl);
        curl_easy_cleanup(curl);

        if(res != CURLE_OK) {
            std::cerr << "GET request failed: " << curl_easy_strerror(res) << std::endl;
        }
    }

    return json::parse(readBuffer);
}

// Function to send POST request
json httpPost(const std::string& url, const json& data) {
    CURL* curl;
    CURLcode res;
    std::string readBuffer;

    curl = curl_easy_init();
    if(curl) {
        curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
        curl_easy_setopt(curl, CURLOPT_POST, 1L);

        // JSON data
        std::string jsonData = data.dump();
        curl_easy_setopt(curl, CURLOPT_POSTFIELDS, jsonData.c_str());

        struct curl_slist* headers = NULL;
        headers = curl_slist_append(headers, "Content-Type: application/json");
        curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);

        curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, WriteCallback);
        curl_easy_setopt(curl, CURLOPT_WRITEDATA, &readBuffer);

        res = curl_easy_perform(curl);
        curl_easy_cleanup(curl);

        if(res != CURLE_OK) {
            std::cerr << "POST request failed: " << curl_easy_strerror(res) << std::endl;
        }
    }

    return json::parse(readBuffer);
}

// Function to send PUT request
json httpPut(const std::string& url, const json& data) {
    CURL* curl;
    CURLcode res;
    std::string readBuffer;

    curl = curl_easy_init();
    if(curl) {
        curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
        curl_easy_setopt(curl, CURLOPT_CUSTOMREQUEST, "PUT");

        std::string jsonData = data.dump();
        curl_easy_setopt(curl, CURLOPT_POSTFIELDS, jsonData.c_str());

        struct curl_slist* headers = NULL;
        headers = curl_slist_append(headers, "Content-Type: application/json");
        curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);

        curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, WriteCallback);
        curl_easy_setopt(curl, CURLOPT_WRITEDATA, &readBuffer);

        res = curl_easy_perform(curl);
        curl_easy_cleanup(curl);

        if(res != CURLE_OK) {
            std::cerr << "PUT request failed: " << curl_easy_strerror(res) << std::endl;
        }
    }

    return json::parse(readBuffer);
}

// Function to send PATCH request
json httpPatch(const std::string& url, const json& data) {
    CURL* curl;
    CURLcode res;
    std::string readBuffer;

    curl = curl_easy_init();
    if(curl) {
        curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
        curl_easy_setopt(curl, CURLOPT_CUSTOMREQUEST, "PATCH");

        std::string jsonData = data.dump();
        curl_easy_setopt(curl, CURLOPT_POSTFIELDS, jsonData.c_str());

        struct curl_slist* headers = NULL;
        headers = curl_slist_append(headers, "Content-Type: application/json");
        curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);

        curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, WriteCallback);
        curl_easy_setopt(curl, CURLOPT_WRITEDATA, &readBuffer);

        res = curl_easy_perform(curl);
        curl_easy_cleanup(curl);

        if(res != CURLE_OK) {
            std::cerr << "PATCH request failed: " << curl_easy_strerror(res) << std::endl;
        }
    }

    return json::parse(readBuffer);
}

// Function to send DELETE request
void httpDelete(const std::string& url) {
    CURL* curl;
    CURLcode res;

    curl = curl_easy_init();
    if(curl) {
        curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
        curl_easy_setopt(curl, CURLOPT_CUSTOMREQUEST, "DELETE");

        res = curl_easy_perform(curl);
        curl_easy_cleanup(curl);

        if(res != CURLE_OK) {
            std::cerr << "DELETE request failed: " << curl_easy_strerror(res) << std::endl;
        }
    }
}

int main() {
    std::string baseUrl = "https://jsonplaceholder.typicode.com/users";

    // 1. GET Request - Retrieve a list of users
    std::cout << "GET Request: Fetching users..." << std::endl;
    json users = httpGet(baseUrl);
    std::ofstream file("../key.json");
    file << users.dump(4);
    std::cout << users[0]["address"].dump(4) << std::endl;  // Pretty print the JSON

    // 2. Modify user data (update name)
    json user = users[0];
    user["name"] = "John Doe Updated";
    
    // 3. POST Request - Send the modified user back to the server
    std::cout << "\nPOST Request: Creating a new user..." << std::endl;
    json newUser = httpPost(baseUrl, user);
    std::cout << newUser.dump(4) << std::endl;
    
    // // 4. PUT Request - Update the entire user
    std::string putUrl = baseUrl + "/1";  // Assuming user ID is 1
    std::cout << "\nPUT Request: Updating user 1..." << std::endl;
    json updatedUser = httpPut(putUrl, user);
    std::cout << updatedUser.dump(4) << std::endl;
    
    // 5. PATCH Request - Update a single field of the user
    json patchData;
    patchData["email"] = "updated.email@example.com";
    std::cout << "\nPATCH Request: Updating user's email..." << std::endl;
    json patchedUser = httpPatch(putUrl, patchData);
    std::cout << patchedUser.dump(4) << std::endl;

    // 6. DELETE Request - Remove the user
    std::cout << "\nDELETE Request: Deleting user 1..." << std::endl;
    httpDelete(putUrl);
    std::cout << "User 1 deleted." << std::endl;

    return 0;
}
```