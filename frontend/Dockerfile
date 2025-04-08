FROM node:22-alpine

WORKDIR /app

# 安装依赖
COPY package*.json ./

# 安装依赖
RUN npm install

# 复制源代码
COPY . .

# 创建 .vite-temp 目录并设置权限
RUN mkdir -p /app/node_modules/.vite-temp && \
    chown -R node:node /app && \
    chmod -R 755 /app && \
    chmod -R 777 /app/node_modules


EXPOSE 5173

CMD ["npm", "run", "dev"]

