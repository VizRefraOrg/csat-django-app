variable "az_region" {
  type    = string
  default = "East US"
}

variable "resource_group" {
  default = "django-app"
}

variable "app_name" {
  default = "csat-streamlit-admin"
}

variable "image_name" {
  default = "csat-django-app"
}

#variable "env" {}
#
#variable "git_user" {}
#
#variable "git_branch" {}
