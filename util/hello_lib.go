package util

import "fmt"

func PrintHello() {
	fmt.Printf("Hello World")
}

func PrintWorld() {
	fmt.Printf("World")
}

func ShouldTriggerLint() {
	fmt.Printf("missing func comments")
}

func BrokenCode() {
	fmt.Printf("invalid go"
}
