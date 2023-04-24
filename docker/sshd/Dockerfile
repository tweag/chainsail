FROM python:3.8.7-slim

RUN mkdir -p /run/sshd

RUN apt-get update && \
    apt-get install -y curl wget unzip openssh-client openssh-server && \
    rm -rf /var/lib/apt/lists/*

# Global SSH configurations
RUN sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
# Disable password authentication
RUN sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
# Disable StrictMode (required for k8s secret volumes to work properly since their symlinks have open permissions)
RUN sed -i 's/#StrictModes yes/StrictModes no/' /etc/ssh/sshd_config
# Listen on a non-default port to avoid clashing with the host's ssh
RUN sed -i 's/#Port 22/Port 26/' /etc/ssh/sshd_config
# SSH login fix. Otherwise user is kicked off after login
RUN sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd

ADD ssh/ssh_config /etc/ssh/ssh_config
ADD entrypoint.sh /app/entrypoint.sh

# For SSH. Using non-default ssh port.
EXPOSE 26

ENTRYPOINT ["/app/entrypoint.sh"]
