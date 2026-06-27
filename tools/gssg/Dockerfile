# 一次性静态站点生成器:ghost-static-site-generator(gssg)
# 抓取本地运行的 Ghost,产出静态 HTML 到 /site/static(挂载到宿主 ./static)。
# 放在容器里跑,宿主机无需安装 wget/node,保持环境干净。
FROM node:22-alpine

RUN apk add --no-cache wget bash
RUN npm install -g ghost-static-site-generator@1.1.4

WORKDIR /site

# gssg 默认抓取 http://localhost:2368(与 Ghost 的 url 一致),输出到 ./static。
# --url 把站内绝对链接改写成最终发布地址(GitHub Pages / 自定义域名)。
CMD ["sh", "-c", "gssg --url \"$PAGES_URL\" && echo 'static site generated -> ./static'"]
