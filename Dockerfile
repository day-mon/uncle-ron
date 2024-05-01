# Caching: https://stackoverflow.com/questions/58593661/slow-gradle-build-in-docker-caching-gradle-build

# Downloads gradle w/ java
FROM gradle:8.5-jdk-alpine as cache

# Creates cache home
RUN mkdir -p /home/gradle/cache_home

# Sets GRADLE_USER_HOME to here so it can write the dependencies here instead of normal gradle home
ENV GRADLE_USER_HOME /home/gradle/cache_home

# Copies build file
COPY build.gradle.kts /home/gradle/java-code/

# Sets Workdirectory moves
WORKDIR /home/gradle/java-code

# Builds project
RUN gradle clean build -i --stacktrace


# Downloads gradle w/ java
FROM gradle:8.5-jdk-alpine as builder

# Copies depenencies to actual GRADLE_USER_HOME so it doesnt need to redownload here...
# Normal GRADLE_USER_HOME = /home/gradle/.gradle. Its changed so you wont need to have gradle installed for it to persist
COPY --from=cache /home/gradle/cache_home /home/gradle/.gradle

# Copies all files from project into /home/uncle-ron
COPY . /home/uncle-ron

# Sets work directory moves
WORKDIR /home/uncle-ron

# Jars project
RUN gradle bootJar -i --stacktrace

# Downloads java
FROM  openjdk:21-slim

# Sets user to root
USER root

# Sets work directory moves
WORKDIR /home/uncle-ron

# Copies jar from builder build steps
COPY --from=builder /home/uncle-ron/build/libs/UncleRon.jar ./app.jar

# Runs.. :)
ENTRYPOINT java -jar -Xmx2G app.jar