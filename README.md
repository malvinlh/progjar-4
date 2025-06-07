# progjar-4

Tugas 4 Pemrograman Jaringan (D) 2025 adalah implementasi server HTTP/1.0 berbasis Python yang ringan, beserta klien baris perintah (CLI), dengan dukungan operasi berkas (list, upload, delete) dan dua mode konkurensi (thread-pool dan process-pool). Seluruh komponen dijalankan di **localhost**, artinya server dan klien berjalan pada mesin yang sama.

Tugas ini menunjukkan cara:

- Menyajikan isi direktori (`GET /some/dir/`)  
- Mengunggah berkas (`POST /upload/<filename>`)  
- Menghapus berkas (`DELETE /<filename>`)  
- Menjalankan server dalam mode **thread-pool** dan **process-pool**

File utama yang digunakan:

- `http.py`  
- `server_thread_pool_http.py`  
- `server_process_pool_http.py`  
- `client/client_advanced.py`



## Cara Menjalankan

### 1. Jalankan Salah Satu Mode Server
- Thread-Pool (port 8885)
  
  ```bash
  python3 server_thread_pool_http.py
  ```
  
- Process-Pool (port 8889)

  ```bash
  python3 server_process_pool_http.py
  ```

### 2. Jalankan Klien CLI

Masuk ke `client/` dan jalankan operasi list, upload, dan delete seperti contoh di bawah ini:

- List File pada Satu Direktori
  
  ```bash
  python3 client_advanced.py localhost:8885 list /
  ```

- Upload File

  ```bash
  python3 client_advanced.py localhost:8885 upload ../lokal.pdf client/nama_remote.pdf
  ```

- Delete File

  ```bash
  python3 client_advanced.py localhost:8885 delete client/nama_remote.pdf
  ```
