#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netdb.h>
#include <unistd.h>
#include <errno.h>

#define BUFFER_SIZE 4096

void error(const char *msg)
{
    perror(msg);
    exit(EXIT_FAILURE);
}

int perform_get(const char *hostname, const char *path, const char *port)
{
    struct addrinfo hints, *result, *rp;
    int s, sockfd;

    memset(&hints, 0, sizeof(struct addrinfo));
    hints.ai_family = AF_UNSPEC; /* Allow IPv4 or IPv6 */
    hints.ai_socktype = SOCK_STREAM;
    hints.ai_flags = 0;
    hints.ai_protocol = 0;

    s = getaddrinfo(hostname, port, &hints, &result);
    if (s != 0)
    {
        fprintf(stderr, "getaddrinfo: %s: %s\n", gai_strerror(s), hostname);
        return 1;
    }

    for (rp = result; rp != NULL; rp = rp->ai_next)
    {
        sockfd = socket(rp->ai_family, rp->ai_socktype, rp->ai_protocol);
        if (sockfd == -1)
            continue;

        if (connect(sockfd, rp->ai_addr, rp->ai_addrlen) != -1)
            break;
        close(sockfd);
    }

    if (rp == NULL)
    {
        fprintf(stderr, "error connecting to %s:%s\n", hostname, port);
        return 1;
    }

    freeaddrinfo(result);

    char request[BUFFER_SIZE];
    snprintf(request, sizeof(request),
             "GET %s HTTP/1.1\r\n"
             "Host: %s\r\n"
             "Metadata-Flavor: Google\r\n"
             "Connection: close\r\n"
             "\r\n",
             path, hostname);

    if (write(sockfd, request, strlen(request)) < 0)
        error("error writing to socket\n");

    char response[BUFFER_SIZE];
    ssize_t n;

    while ((n = read(sockfd, response, BUFFER_SIZE - 1)) > 0)
    {
        response[n] = '\0';
        const char *crlf = strstr(response, "\r\n\r\n");
        if (crlf)
        {
            printf("%s", crlf + 4);
            break;
        }
    }

    if (n < 0)
        error("reading from socket\n");

    close(sockfd);
    return 0;
}

int main(int argc, char *argv[])
{
    int error;
    error = perform_get("metadata.google.internal", "/computeMetadata/v1/instance/network-interfaces/0/access-configs/0/external-ip", "80");
    if (error)
    {
        error = perform_get("api.ipify.org", "/", "80");
        if (error)
            exit(EXIT_FAILURE);
    }
    return 0;
}
