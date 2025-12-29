package main

import (
	"encoding/json"
	"fmt"
	"math"
	"net/http"
	"time"
)

// GetNthPrime calculates the nth prime number
func GetNthPrime(n int) int {
	count := 0
	num := 2
	for count < n {
		isPrime := true
		sqrtNum := int(math.Sqrt(float64(num)))
		for i := 2; i <= sqrtNum; i++ {
			if num%i == 0 {
				isPrime = false
				break
			}
		}
		if isPrime {
			count++
		}
		if count < n {
			num++
		}
	}
	return num
}

func heavyHandler(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	nth := 20000 // Calculate 20,000th prime

	prime := GetNthPrime(nth)

	duration := time.Since(start)

	response := map[string]interface{}{
		"Message":    fmt.Sprintf("Found %dth prime number", nth),
		"Result":     prime,
		"DurationMs": float64(duration.Milliseconds()),
		"Platform":   "Go",
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

func ioHandler(w http.ResponseWriter, r *http.Request) {
	// Simulate I/O delay
	time.Sleep(100 * time.Millisecond)

	response := map[string]string{
		"Message":  "I/O Operation Complete",
		"Platform": "Go",
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

func main() {
	http.HandleFunc("/heavy", heavyHandler)
	http.HandleFunc("/io", ioHandler)

	fmt.Println("Go server running on port 8080...")
	if err := http.ListenAndServe(":8080", nil); err != nil {
		fmt.Printf("Error starting server: %s\n", err)
	}
}
