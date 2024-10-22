# python-skeleton-template

## 1. How to run locally?

- Setup environment - required packages:
  - python `^3.10`
  - poetry `1.8.2`
  - Docker `23.0.5`
  - pre-commit `4.6.0`
  - ruff `0.4.3`
  - direnv `2.32.2` [`optional`]


  ```shell
  brew install pre-commit ruff
  ```

- Create `python` virtual environment
  ```shell
  make install
  ```

- Config `pre-commit` - one time setup
  ```shell
  pre-commit install
  ```

  ```shell
  pre-commit run --all-files
  ```

- Copy `.example.env` to `.env` in same project directory if any
  ```shell
  cp .example.env .env
  ```

## 2. How to run locally via `Docker`?

- Build `Docker` image
  ```shell
  make build_local
  ```

- Run `Docker` container
  ```shell
  make run_local
  ```
