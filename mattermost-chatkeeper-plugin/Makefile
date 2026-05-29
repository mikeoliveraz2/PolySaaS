# ChatKeeper Plugin Makefile

.PHONY: build build-server build-webapp clean deploy

PLUGIN_ID=com.polysaas.chatkeeper
BUNDLE_NAME=chatkeeper.tar.gz

# Build everything
build: build-server build-webpack
	@echo "Creating plugin bundle..."
	@rm -rf dist/
	@mkdir -p dist
	@cp plugin.json dist/
	@cp -r server/dist dist/server
	@cp -r webapp/dist dist/webapp
	@cd dist && tar -czvf ../$(BUNDLE_NAME) .
	@echo "Build complete: $(BUNDLE_NAME)"

# Build server component
build-server:
	@echo "Building server..."
	@cd server && go mod tidy
	@cd server && mkdir -p dist
	@cd server && GOOS=linux GOARCH=amd64 go build -o dist/plugin-linux-amd64
	@cd server && GOOS=linux GOARCH=arm64 go build -o dist/plugin-linux-arm64
	@cd server && GOOS=darwin GOARCH=amd64 go build -o dist/plugin-darwin-amd64
	@cd server && GOOS=darwin GOARCH=arm64 go build -o dist/plugin-darwin-arm64
	@cd server && GOOS=windows GOARCH=amd64 go build -o dist/plugin-windows-amd64.exe

# Build webapp component
build-webapp:
	@echo "Building webapp..."
	@cd webapp && npm install
	@cd webapp && npm run build

# Clean build artifacts
clean:
	@echo "Cleaning..."
	@rm -rf dist/
	@rm -rf server/dist/
	@rm -rf webapp/dist/
	@rm -rf webapp/node_modules/
	@rm -f $(BUNDLE_NAME)

# Quick development build (current platform only)
dev:
	@cd server && go build -o dist/plugin-linux-amd64
	@cd webapp && npm run build:dev

# Deploy to Mattermost (requires MM_SERVICESETTINGS_SITEURL and MM_ADMIN_TOKEN)
deploy:
	@echo "Deploying to Mattermost..."
	@if [ -z "$(MM_SERVICESETTINGS_SITEURL)" ] || [ -z "$(MM_ADMIN_TOKEN)" ]; then \
		echo "Error: MM_SERVICESETTINGS_SITEURL and MM_ADMIN_TOKEN must be set"; \
		exit 1; \
	fi
	@./scripts/deploy.sh $(PLUGIN_ID) $(BUNDLE_NAME)

# Run tests
test:
	@cd server && go test -v ./...

# Format code
fmt:
	@cd server && go fmt ./...

# Check for issues
lint:
	@cd server && go vet ./...
