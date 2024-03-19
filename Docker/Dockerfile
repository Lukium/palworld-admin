# Use Ubuntu 23.10 as the base image
FROM ubuntu:23.10

# Apply Labels
LABEL   org.opencontainers.image.title="Palworld ADMIN" \
        org.opencontainers.image.description="Palworld Dedicated Server Management Tool" \
        org.opencontainers.image.url="https://github.com/Lukium/palworld-admin" \
        org.opencontainers.image.source="https://github.com/Lukium/palworld-admin" \
        org.opencontainers.image.version="0.1.0" \
        org.opencontainers.image.vendor="Lukium Swarm" \
        org.opencontainers.image.licenses="Non-Commercial Use Only"
    
# Avoid prompts from apt to be interactive
ARG DEBIAN_FRONTEND=noninteractive    

# Install sudo, make lukium a passwordless sudoer and create its relevant directories
RUN	apt-get update && \
	apt-get install -y sudo && \
	# Create a non-root user 'lukium'
	useradd -m lukium && \
        # Make lukium a passwordless sudoer, this is so that the container can auto-update Wine later
	echo 'lukium ALL=(ALL) NOPASSWD: ALL' > /etc/sudoers.d/lukium && \
        # Ensure the sudoers file has correct permissions
    	chmod 0440 /etc/sudoers.d/lukium && \
        # Give lukium ownership of the relevant directories
        mkdir -p /home/lukium/palworld-admin && \        
        chown -R lukium:lukium /home/lukium/palworld-admin

# Set the working directory to the application directory
WORKDIR /home/lukium/palworld-admin

# Copy the entrypoint script to the application directory
COPY --chown=lukium:lukium entrypoint.sh /home/lukium/entrypoint.sh

# Make the entrypoint script executable
RUN chmod +x /home/lukium/entrypoint.sh

# Switch to the non-root user 'lukium'
USER lukium

# Add the i386 architecture, install necessary packages, add the WineHQ repository, install Wine and Winetricks, use xvfb
RUN     sudo dpkg --add-architecture i386 && \
        sudo apt-get update && \
        sudo apt-get install -y nano wget gnupg2 software-properties-common curl xvfb && \
        sudo mkdir -pm755 /etc/apt/keyrings && \
        sudo wget -O /etc/apt/keyrings/winehq-archive.key https://dl.winehq.org/wine-builds/winehq.key && \
        sudo wget -NP /etc/apt/sources.list.d/ https://dl.winehq.org/wine-builds/ubuntu/dists/mantic/winehq-mantic.sources && \
        sudo apt-get update && \
        sudo apt-get install --install-recommends winehq-devel winetricks -y && \        
	# Now as 'lukium', use xvfb-run and winetricks under this user
	set -xe && \
	export WINEDEBUG=-all && \
        WINEDLLOVERRIDES="mscoree,mshtml=" xvfb-run wine wineboot && \
        xvfb-run wineserver -w && \
        xvfb-run winetricks -q corefonts vcrun2022 && \        
        # Now cleanup stuff that's no longer needed
        sudo apt-get remove -y xvfb winetricks && \
        sudo apt-get autoremove -y && \
        sudo apt-get clean && \
        sudo rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* && \
        # Create the SteamCMD directory and give 'lukium' ownership
        sudo mkdir -p /home/lukium/.wine/drive_c/steamcmd && \
        sudo chown -R lukium:lukium /home/lukium/.wine/drive_c/steamcmd

# Document that the service listens on specific ports
EXPOSE 8210/tcp 8211/udp 25575/tcp 27015/udp

# Setup Volumes
VOLUME ["/home/lukium/palworld-admin", "/home/lukium/.wine/drive_c/steamcmd"]

# Setup Environment Variables
ENV MANAGEMENT_PASSWORD="palworld-admin-123"
ENV MANAGEMENT_PORT="8210"

# Use the custom entrypoint script as 'lukium'
ENTRYPOINT ["/home/lukium/entrypoint.sh"]
