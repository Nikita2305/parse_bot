# demhack

## To prepare
`./scripts/setup.sh`

And also add file `demhack/demhack/credentials.json` with the following structure:
```json
{
"admin_id": "ADMIN_TG_ID",
"bot_token": "TG_BOT_TOKEN"
}
```

## To run the bot
`./scripts/start.sh`

## To login tg-account
`./scripts/login.sh path/to/tg_config_name.config`

Where tg_config_name.config has structure:

```json
{
"phone": "PASTE_PHONE",
"api_id": "PASTE_API_ID",
"api_hash": "PASTE_API_HASH"
}
```

Or, if you have password as second-factor authentication unit:

```json
{
"phone": "PASTE_PHONE",
"api_id": "PASTE_API_ID",
"api_hash": "PASTE_API_HASH",
"password": "PASTE_2FA_PASSWORD"
}
```
