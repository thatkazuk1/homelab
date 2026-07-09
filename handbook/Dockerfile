FROM python:3.12-slim AS builder

WORKDIR /src

RUN pip install --no-cache-dir mkdocs-material==9.7.6

COPY . .

RUN mkdocs build --strict --clean --site-dir /site

FROM nginx:alpine

COPY --from=builder /site /usr/share/nginx/html

COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
