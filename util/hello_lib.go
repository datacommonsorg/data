package util

import "fmt"

func Hello() string {
	return "Hello World"
}

func PrintHello() {
	fmt.Printf("Hello World")
}

func PrintWorld() {
	fmt.Printf("World")
}

func ShouldTriggerLint() {
	fmt.Printf("missing func comments")
}
