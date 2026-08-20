bind = "0.0.0.0:10000"
workers = 1
threads = 2
timeout = 300  # ✅ Increase timeout to 5 minutes
worker_class = "gthread"
keepalive = 5
graceful_timeout = 30
