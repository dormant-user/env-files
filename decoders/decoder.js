const crypto = require('crypto');
const axios = require('axios');

const APIKEY = process.env.APIKEY;

async function transitDecrypt(ciphertext, keyLength = 32) {
    const epoch = Math.floor(Date.now() / 60000);
    const hash = crypto.createHash('sha256');
    hash.update(`${epoch}.${APIKEY}`);
    const aesKey = hash.digest().slice(0, keyLength);

    const bufferCiphertext = Buffer.from(ciphertext, 'base64');
    if (bufferCiphertext.length < 12 + 16) {
        throw new Error('Ciphertext is too short');
    }

    const iv = bufferCiphertext.slice(0, 12); // First 12 bytes
    const authTag = bufferCiphertext.slice(bufferCiphertext.length - 16); // Last 16 bytes
    const encryptedData = bufferCiphertext.slice(12, bufferCiphertext.length - 16); // Data in between

    const decipher = crypto.createDecipheriv('aes-256-gcm', aesKey, iv);
    decipher.setAuthTag(authTag); // Set the authentication tag

    let decrypted;
    try {
        decrypted = Buffer.concat([decipher.update(encryptedData), decipher.final()]);
    } catch (err) {
        throw new Error('Decryption failed: ' + err.message);
    }

    return JSON.parse(decrypted.toString());
}

async function getCipher() {
    const headers = {
        'accept': 'application/json',
        'Authorization': `Bearer ${APIKEY}`,
    };
    const params = {
        table_name: 'default',
    };
    const response = await axios.get('http://0.0.0.0:8080/get-table', {params, headers});
    if (response.status !== 200) {
        throw new Error(response.data);
    }
    return response.data.detail;
}

async function main() {
    try {
        const ciphertext = await getCipher();
        const result = await transitDecrypt(ciphertext);
        console.log(result);
    } catch (error) {
        console.error(error);
    }
}

main();
