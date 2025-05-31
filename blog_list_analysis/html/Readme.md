下面给出几种常用的静态文件部署方式，您可以根据自己的环境和需求任选其一。

一、Python 内置 HTTP 服务器（开发/小规模演示）
1. 进入项目根目录（包含 index.html、style.css、script.js、data.json）
2. 运行：
   ```bash
   # Python 3.x
   python3 -m http.server 8000
   ```
3. 浏览器打开 http://localhost:8000 即可访问

二、Node.js + http-server（开发/小规模演示）
1. 安装全局 http-server：
   ```bash
   npm install -g http-server
   ```
2. 在项目根目录启动服务：
   ```bash
   http-server -p 8000
   ```
3. 浏览器打开 http://localhost:8000

三、使用 Nginx（生产环境推荐）
1. 将项目打包后的静态文件（index.html、style.css、script.js、data.json）拷贝到服务器，假设放在 /var/www/blog-dashboard
2. 编辑 /etc/nginx/sites-available/blog-dashboard.conf：
   ```
   server {
     listen       80;
     server_name  your.domain.com;      # 改成你的域名或 IP
     root   /var/www/blog-dashboard;
     index  index.html;
     location / {
       try_files $uri $uri/ =404;
     }
   }
   ```
3. 启用配置并重载：
   ```bash
   ln -s /etc/nginx/sites-available/blog-dashboard.conf /etc/nginx/sites-enabled/
   nginx -t && systemctl reload nginx
   ```
4. 浏览器访问 http://your.domain.com

四、Docker + Nginx 容器化部署
1. 在项目根目录建一个 Dockerfile：
   ```dockerfile
   FROM nginx:alpine
   COPY . /usr/share/nginx/html
   # 可选：拷贝自定义 nginx.conf 覆盖 /etc/nginx/conf.d/default.conf
   EXPOSE 80
   ```
2. 构建镜像并运行容器：
   ```bash
   docker build -t blog-dashboard .
   docker run -d --name blog-dashboard -p 80:80 blog-dashboard
   ```
3. 在任何可以访问到宿主机 80 端口的地方打开浏览器即可

五、GitHub Pages / GitLab Pages（托管在代码仓库）
1. 将项目（四个文件）推到 GitHub 仓库的 `gh-pages` 分支或 `docs/` 目录
2. 在仓库设置里开启 GitHub Pages，指向对应目录
3. 若使用 GitLab，创建 `.gitlab-ci.yml`：
   ```yaml
   image: node:16
   pages:
     stage: deploy
     script:
       - npm install -g http-server
       - http-server -p 8080 -c-1 . & sleep 2
     artifacts:
       paths:
         - public
     only:
       - main
   ```
4. 推送后自动生成 pages 地址

总结
- 开发测试：`python -m http.server` 或 `http-server`
- 生产建议：Nginx 或 Docker+Nginx
- 轻量托管：GitHub Pages / GitLab Pages

根据团队或项目规模选用即可。