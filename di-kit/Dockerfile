FROM docker/sandbox-templates:kiro-docker

USER root

# Install Eclipse Temurin 21
RUN apt-get update \
    && apt-get install -y --no-install-recommends wget apt-transport-https gpg \
    && wget -qO - https://packages.adoptium.net/artifactory/api/gpg/key/public | gpg --dearmor | tee /etc/apt/trusted.gpg.d/adoptium.gpg > /dev/null \
    && echo "deb https://packages.adoptium.net/artifactory/deb $(awk -F= '/^VERSION_CODENAME/{print$2}' /etc/os-release) main" | tee /etc/apt/sources.list.d/adoptium.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends temurin-21-jdk \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set JAVA_HOME to Temurin 21
RUN ln -s /usr/lib/jvm/temurin-21-jdk-$(dpkg --print-architecture) /usr/lib/jvm/temurin-21
ENV JAVA_HOME=/usr/lib/jvm/temurin-21
ENV PATH="${JAVA_HOME}/bin:${PATH}"

# Install Android SDK command-line tools
ENV ANDROID_HOME=/opt/android-sdk
ENV PATH="${ANDROID_HOME}/cmdline-tools/latest/bin:${ANDROID_HOME}/platform-tools:${PATH}"

RUN mkdir -p ${ANDROID_HOME}/cmdline-tools \
    && cd /tmp \
    && curl -fsSL https://dl.google.com/android/repository/commandlinetools-linux-14742923_latest.zip -o cmdline-tools.zip \
    && unzip -q cmdline-tools.zip \
    && mv cmdline-tools ${ANDROID_HOME}/cmdline-tools/latest \
    && rm cmdline-tools.zip

# Accept licences and install platform-tools and build-tools
RUN yes | sdkmanager --sdk_root=${ANDROID_HOME} --licenses > /dev/null 2>&1 \
    && sdkmanager --sdk_root=${ANDROID_HOME} "platform-tools" "build-tools;35.0.0" "build-tools;37.0.0"

# Install ARM64 native build-tools (aapt2, aidl, zipalign, split-select)
# Google only ships x86_64 binaries; this provides arm64 replacements
RUN curl -fsSL https://raw.githubusercontent.com/Commit451/android-arm-build-tools/main/install.sh | bash

COPY files/home/.gradle/gradle.properties /home/agent/.gradle/gradle.properties
RUN chown -R 1000:1000 /home/agent/.gradle

# Make SDK writable by agent user so Gradle can download additional components
RUN chown -R 1000:1000 ${ANDROID_HOME}

USER agent
