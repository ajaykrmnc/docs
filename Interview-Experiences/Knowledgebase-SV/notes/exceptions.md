## Exceptions in C++

- Ignoring exception: Leads to core dump
- What is exception: 
    - Something that gets thrown
    - Something that gets caught (hopefully)
- Throwing and catching exceptions is `expensive`.

- If an exception is thrown:
    - During stack unwinding the program is terminated
    - Caught by a matching handler
    - All the intermediate objects in stack are destructed
    - If no matching handler is found, the functions `std::terminate` is called

- Desctructor throwing exception:
    - Bad situation
    - If an exception is thrown while another exception is already being 
    handled, this causes terminate to be called, which ends the program 
    abruptly. This occurs because C++ cannot handle two simultaneous exceptions.
	- For example, if an exception is thrown and the stack unwinds to destroy 
    objects in scope, any destructor that throws an exception will clash with 
    the already active exception.

- Handle the exception there itself (for Destructors)
    ```cpp
    struct ResourceHandler {
        ~ResourceHandler() {
            try {
                // Code that may throw an exception
                cleanup();
            } catch (const std::exception& e) {
                // Handle or log the exception, but do not rethrow
                std::cerr << "Exception in destructor: " << e.what() << std::endl;
            } catch (...) {
                std::cerr << "Unknown exception in destructor" << std::endl;
            }
        }
        
        void cleanup() {
            // Code that might throw an exception
        }
    };
    ```

- Exception Hygiene
    - Throw by value [*This memory is allocated on heap 
     actually, therefore expensive*]
    - Catch by (const) reference


**Custom Exception in C++:**

```cpp
#include <iostream>
#include <exception>
#include <string>

// Step 1: Define the custom exception class
class MyCustomException : public std::exception {
private:
    std::string message;  // Custom error message

public:
    // Constructor to initialize the error message
    MyCustomException(const std::string& msg) : message(msg) {}

    // Override the what() function
    virtual const char* what() const noexcept override {
        return message.c_str();
    }
};

// Function that may throw MyCustomException
void riskyFunction(bool triggerError) {
    if (triggerError) {
        throw MyCustomException("Something went wrong in riskyFunction!");
    }
    std::cout << "Function executed successfully." << std::endl;
}

int main() {
    try {
        // Step 2: Call the function and trigger the custom exception
        riskyFunction(true);  // Pass true to trigger the exception
    }
    catch (const MyCustomException& e) {  // Step 3: Catch the custom exception
        std::cerr << "Caught custom exception: " << e.what() << std::endl;
    }
    return 0;
}
```
**Re-throwing:**

Inside a catch block, using throw; without any argument will 
rethrow the currently caught exception. This is often done to 
perform some actions (like logging) and then pass the 
exception up the stack without changing it.

```cpp
#include <iostream>
#include <exception>

void innerFunction() {
    throw std::runtime_error("Error in innerFunction");  // Throwing an exception
}

void outerFunction() {
    try {
        innerFunction();
    }
    catch (const std::exception& e) {
        std::cerr << "Caught in outerFunction: " << e.what() << std::endl;
        throw;  // Rethrow the same exception to propagate it further
    }
}

int main() {
    try {
        outerFunction();
    }
    catch (const std::exception& e) {
        std::cerr << "Caught in main: " << e.what() << std::endl;
    }
    return 0;
}
```

> Prefer to keep exceptions as "Rare" as you can, meaning for 
serious, uncommon errors

> Resource management should always use RAII
