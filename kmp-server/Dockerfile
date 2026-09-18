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

# Stage 2: run on a small JRE-only Alpine image. Temurin publishes no Alpine JRE 17
# for arm64, so the runtime uses Liberica, which does.
FROM bellsoft/liberica-openjre-alpine:17
WORKDIR /app
COPY --from=build /app/build/install/kmp-server ./

ENV PORT=8080
EXPOSE 8080

USER 1000:1000
ENTRYPOINT ["bin/kmp-server"]
