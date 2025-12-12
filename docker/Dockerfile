FROM ubuntu:22.04

# Avoid interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Install tmux and useful tools
RUN apt-get update && apt-get install -y \
    tmux \
    vim \
    nano \
    tree \
    htop \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user
RUN useradd -m -s /bin/bash learner

# Create sample files for practice
RUN mkdir -p /home/learner/practice && \
    echo "Welcome to tmux-learn sandbox!\n\nThis is a safe environment to practice tmux keybindings.\n\nTry navigating between panes, resizing, and splitting!" > /home/learner/practice/readme.txt && \
    echo "File 1 content\nLine 2\nLine 3" > /home/learner/practice/file1.txt && \
    echo "File 2 content\nAnother line" > /home/learner/practice/file2.txt && \
    echo "File 3 for testing\nYet another line" > /home/learner/practice/file3.txt && \
    mkdir -p /home/learner/practice/subdir && \
    echo "Nested file" > /home/learner/practice/subdir/nested.txt

# Copy entrypoint script (must be readable by all since user is learner)
COPY entrypoint.sh /entrypoint.sh
RUN chmod 755 /entrypoint.sh

# Set ownership
RUN chown -R learner:learner /home/learner

USER learner
WORKDIR /home/learner

# Default tmux config location
ENV HOME=/home/learner

ENTRYPOINT ["/entrypoint.sh"]
CMD ["tmux", "new-session", "-s", "learn"]
