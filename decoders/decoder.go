package main

import (
	"crypto/aes"
	"crypto/cipher"
	"crypto/sha256"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"time"
)

var apiKey = os.Getenv("APIKEY")

func transitDecrypt(ciphertext string, keyLength int) (map[string]interface{}, error) {
	epoch := time.Now().Unix() / 60
	hash := sha256.New()
	hash.Write([]byte(fmt.Sprintf("%d.%s", epoch, apiKey)))
	aesKey := hash.Sum(nil)[:keyLength]

	cipherBytes, err := base64.StdEncoding.DecodeString(ciphertext)
	if err != nil {
		return nil, err
	}

	nonce := cipherBytes[:12]
	cipherText := cipherBytes[12:]

	block, err := aes.NewCipher(aesKey)
	if err != nil {
		return nil, err
	}

	gcm, err := cipher.NewGCM(block)
	if err != nil {
		return nil, err
	}

	decrypted, err := gcm.Open(nil, nonce, cipherText, nil)
	if err != nil {
		return nil, err
	}

	var result map[string]interface{}
	err = json.Unmarshal(decrypted, &result)
	if err != nil {
		return nil, err
	}

	return result, nil
}

func getCipher() (string, error) {
	req, err := http.NewRequest("GET", "http://0.0.0.0:8080/get-table", nil)
	if err != nil {
		return "", err
	}

	req.Header.Set("Accept", "application/json")
	req.Header.Set("Authorization", "Bearer "+apiKey)
	q := req.URL.Query()
	q.Add("table_name", "default")
	req.URL.RawQuery = q.Encode()

	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return "", fmt.Errorf("HTTP error: %s", resp.Status)
	}

	var response struct {
		Detail string `json:"detail"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&response); err != nil {
		return "", err
	}

	return response.Detail, nil
}

func main() {
	ciphertext, err := getCipher()
	if err != nil {
		fmt.Println("Error getting cipher:", err)
		return
	}

	decryptedData, err := transitDecrypt(ciphertext, 32)
	if err != nil {
		fmt.Println("Error decrypting:", err)
		return
	}

	fmt.Println("Decrypted data:", decryptedData)
}
