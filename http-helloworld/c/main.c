#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <sys/select.h>
#include <errno.h>

#define PORT 9000
#define MAX_CLIENTS 10
#define BUFFER_SIZE 1024


void handle_client(int client_socket) {
    char buffer[BUFFER_SIZE];
    int bytes_received;

    bytes_received = recv(client_socket, buffer, BUFFER_SIZE - 1, 0);
    if (bytes_received < 0) {
        perror("recv() failed");
        close(client_socket);
        return;
    }
    buffer[bytes_received] = '\0';

    printf("received request:\n---\n%s\n---\n", buffer);

    const char *response = "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: 12\r\n\r\nhello world!";
    int n = send(client_socket, response, strlen(response), 0);
    if (n < 0) {
        perror("send() failed");
    }
    printf("sent response: %d\n", n);
}

int main() {
    int server_socket, client_socket;
    struct sockaddr_in server_address, client_address;
    socklen_t client_address_len = sizeof(client_address);
    fd_set read_fds;
    int max_fd;

    server_socket = socket(AF_INET, SOCK_STREAM, 0);
    if (server_socket < 0) {
        perror("socket() failed");
        exit(1);
    }

    memset(&server_address, 0, sizeof(server_address));
    server_address.sin_family = AF_INET;
    server_address.sin_addr.s_addr = INADDR_ANY;
    server_address.sin_port = htons(PORT);

    if (bind(server_socket, (struct sockaddr *)&server_address, sizeof(server_address)) < 0) {
        perror("bind() failed");
        close(server_socket);
        exit(1);
    }

    if (listen(server_socket, MAX_CLIENTS) < 0) {
        perror("listen() failed");
        close(server_socket);
        exit(1);
    }

    printf("listening on port %d\n\n", PORT);

    client_socket = socket(AF_INET, SOCK_STREAM, 0);
    if (client_socket < 0) {
        perror("socket() failed");
        exit(1);
    }

    if (connect(client_socket, (struct sockaddr *)&server_address, sizeof(server_address)) < 0) {
        perror("connect() failed");
        close(client_socket);
        exit(1);
    }

    const char *request = "GET / HTTP/1.1\r\nHost: localhost\r\n\r\n";
    int n = send(client_socket, request, strlen(request), 0);
    if (n < 0) {
        perror("send() failed");
        close(client_socket);
        exit(1);
    }
    printf("sent request: %d\n", n);

    while (1) {
        FD_ZERO(&read_fds);
        FD_SET(server_socket, &read_fds);
        FD_SET(client_socket, &read_fds);
        max_fd = (server_socket > client_socket) ? server_socket : client_socket;

        if (select(max_fd + 1, &read_fds, NULL, NULL, NULL) < 0) {
            perror("select() failed");
            close(server_socket);
            close(client_socket);
            break;
        }

        if (FD_ISSET(server_socket, &read_fds)) {
            printf("! client connected\n");
            int accepted_client_socket = accept(server_socket, (struct sockaddr *)&client_address, &client_address_len);
            if (accepted_client_socket < 0) {
                perror("accept() failed");
                continue;
            }
            handle_client(accepted_client_socket);
            close(accepted_client_socket);
            printf("! client disconnected\n");
        }

        if (FD_ISSET(client_socket, &read_fds)) {
            char buffer[BUFFER_SIZE];
            int bytes_received = recv(client_socket, buffer, BUFFER_SIZE - 1, 0);
            if (bytes_received < 0) {
                perror("recv() failed");
                break;
            } else if (bytes_received == 0) {
                printf("connection closed by server\n");
                break;
            } else {
                buffer[bytes_received] = '\0';
                printf("received response:\n---\n%s\n---\n", buffer);
                break; 
            }
        }
    }

    close(client_socket);
    close(server_socket);

    return 0;
}