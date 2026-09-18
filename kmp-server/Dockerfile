# Stage 1: build with the Gradle wrapper on a full JDK
FROM eclipse-temurin:17-jdk AS build
WORKDIR /app

# Wrapper and build scripts first, so the Gradle download and dependency
# resolution are cached as long as these files do not change
COPY gradlew settings.gradle.kts build.gradle.kts gradle.properties ./
COPY gradle ./gradle
RUN ./gradlew --no-daemon dependencies --quiet > /dev/null

COPY src ./src
RUN ./gradlew --no-daemon installDist

# Stage 2: run on distroless Java. No shell or package manager, runs as uid 65532 (nonroot).
# Its entrypoint is `java -jar`, which the Gradle start script cannot use, so the classpath
# is passed explicitly instead.
FROM gcr.io/distroless/java17-debian12:nonroot
WORKDIR /app
COPY --from=build /app/build/install/kmp-server/lib ./lib

ENV PORT=8080
EXPOSE 8080

ENTRYPOINT ["java", "-cp", "/app/lib/*", "dev.abc.server.ApplicationKt"]
