provider "azurerm" {
  features {}
  subscription_id = "feccbc81-13f1-458a-bf85-cebe2dacca58"
}

data "azurerm_resource_group" "django-app" {
  name = var.resource_group
}

resource "azurerm_container_registry" "django-ui" {
  name                = "csatdjangoacr"
  resource_group_name = data.azurerm_resource_group.django-app.name
  location            = data.azurerm_resource_group.django-app.location
  sku                 = "Premium"
  admin_enabled       = false
}

# Create the Linux App Service Plan
resource "azurerm_service_plan" "django-appserviceplan" {
  name                = var.app_name
  location            = data.azurerm_resource_group.django-app.location
  resource_group_name = data.azurerm_resource_group.django-app.name
  os_type             = "Linux"
  sku_name            = "P1v3"
}

# App settings
locals {
  settings = { for tuple in regexall("(.*?)=['\"]*?(.*)?['\"]*", file("../.env.prod")) : tuple[0] => tuple[1] }
}

# Create App service
resource "azurerm_linux_web_app" "django-webapp" {
  name                = var.app_name
  resource_group_name = data.azurerm_resource_group.django-app.name
  location            = data.azurerm_resource_group.django-app.location
  service_plan_id     = azurerm_service_plan.django-appserviceplan.id
  https_only          = true
  #  client_affinity_enabled = true

  site_config {
    application_stack {
      docker_image     = "${azurerm_container_registry.django-ui.login_server}/${var.image_name}"
      docker_image_tag = "latest"
    }
    container_registry_use_managed_identity = true
    health_check_path                       = "/accounts/heartbeat"
  }

  app_settings = local.settings

  identity {
    type = "SystemAssigned"
  }

}

# add the role to the identity the kubernetes cluster was assigned
resource "azurerm_role_assignment" "appservice_to_acr" {
  scope                = azurerm_container_registry.django-ui.id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_linux_web_app.django-webapp.identity[0].principal_id
}

resource "azurerm_container_registry_webhook" "django-webhook" {
  name                = "mywebhook"
  resource_group_name = data.azurerm_resource_group.django-app.name
  registry_name       = azurerm_container_registry.django-ui.name
  location            = data.azurerm_resource_group.django-app.location

  service_uri = "https://${azurerm_linux_web_app.django-webapp.site_credential.0.name}:${azurerm_linux_web_app.django-webapp.site_credential.0.password}@${azurerm_linux_web_app.django-webapp.name}.scm.azurewebsites.net/api/registry/webhook"
  status      = "enabled"
  scope       = "${var.image_name}:*"
  actions     = ["push"]
}
