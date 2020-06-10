package util

import (
	"testing"
)

func TestHello(t *testing.T) {
	tests := []struct {
		want string
	}{
		{want: "Hello World"},
	}

	for _, test := range tests {
		if got := Hello(); got != test.want {
			t.Errorf("Hello() = %v, want %v", got, test.want)
		}
	}
}
