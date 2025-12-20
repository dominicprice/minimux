.PHONY: dev
dev:
	@echo "running database migrations..."
	@echo "no migrations to run"
	@echo "database up"
	@while true; do sleep 1s; done


.PHONY: status
status:
	@printf "active connections: %d\nrequests (1m): %d\nlatency: %dms" \
		"$$(( RANDOM % 20))" \
		"$$(( RANDOM % 50 ))" \
		"$$(( RANDOM % 999 ))"
