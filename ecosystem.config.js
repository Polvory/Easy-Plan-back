module.exports = {
    apps: [{
        name: "my-python-app",
        script: "server.py",
        interpreter: "python3",
        env: {
            NODE_ENV: "production",
            PYTHONPATH: ".",
            DATABASE_URL: "postgresql://user:pass@localhost/db"
        },
        watch: true,
        ignore_watch: ["venv", ".git", "node_modules"],
        max_memory_restart: "500M"
    }]
}