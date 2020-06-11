package util

import "fmt"

func Hello() string {
	var x string

	return "Hello World"
}

func PrintHello() {
	fmt.Printf("Hello World")
}

func PrintWorld() {
	fmt.Printf(  "World")
}

func ShouldTriggerLint() {
		fmt.Printf("missing func comments")
}
