# Use Node.js 21 alpine image
FROM node:22-alpine

# Set working directory
WORKDIR /app

# Upgrade npm to latest
RUN npm install -g npm@latest

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy app source
COPY . .

# Expose port
EXPOSE 5173

# Start development server
CMD ["npm", "run", "dev", "--", "--host"]