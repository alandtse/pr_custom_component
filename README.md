# PR Custom Component

[![GitHub Release][releases-shield]][releases]
![GitHub all releases][download-all]
![GitHub release (latest by SemVer)][download-latest]
[![GitHub Activity][commits-shield]][commits]

[![License][license-shield]][license]

[![hacs][hacsbadge]][hacs]
![Project Maintenance][maintenance-shield]
[![BuyMeCoffee][buymecoffeebadge]][buymecoffee]

[![Discord][discord-shield]][discord]
[![Community Forum][forum-shield]][forum]

Create a custom component from a Home Assistant Integration Pull Request. Use this when you want to test a pull request that changes a built in integration.

**Warning: This is experimental and may fail if the Pull Request is for a substantially different version of HA or modifies more than the integration. Do not report bugs to the core authors!**

| Platform        | Description                                                     |
| --------------- | --------------------------------------------------------------- |
| `binary_sensor` | Show whether the Pull Request has been updated since install.   |
| `sensor`        | Show's the timestamp of the last change to the Pull Request     |
| `switch`        | Enable to automatically update to the latest on the next check. |

## Installation

0. Use HACS after adding this `https://github.com/alandtse/pr_custom_component` as a custom repository. Skip to 7.
1. If no HACS, use the tool of choice to open the directory (folder) for your HA configuration (where you find `configuration.yaml`).
2. If you do not have a `custom_components` directory (folder) there, you need to create it.
3. In the `custom_components` directory (folder) create a new folder called `pr_custom_component`.
4. Download _all_ the files from the `custom_components/pr_custom_component/` directory (folder) in this repository.
5. Place the files you downloaded in the new directory (folder) you created.
6. Restart Home Assistant.
7. In the HA UI go to "Configuration" -> "Integrations" click "+" and search for "PR Custom Component"

Using your HA configuration directory (folder) as a starting point you should now also have this:

```text
custom_components/pr_custom_component/translations/en.json
custom_components/pr_custom_component/__init__.py
custom_components/pr_custom_component/api.py
custom_components/pr_custom_component/binary_sensor.py
custom_components/pr_custom_component/config_flow.py
custom_components/pr_custom_component/const.py
custom_components/pr_custom_component/manifest.json
custom_components/pr_custom_component/sensor.py
custom_components/pr_custom_component/switch.py
```

## Installing an Auto Generated Custom Component

1. In the HA UI go to "Configuration" -> "Integrations" click "+" and search for "PR Custom Component".
2. Provide the URL of the pull request you want to turn into a custom_component.
   > For example, this will get a Tesla Pull Request: `https://github.com/home-assistant/core/pull/46558`
3. After succesful install, you should see the PR Custom Component with title `Tesla`.
4. Restart Home Assistant to enable the `Tesla` Custom Component to override the default.
5. Hard refresh your browser to download any changes strings.
6. Install `Tesla` Custom Component which has replaced the built in component.

## Upgrading an Auto Generated Custom Component

1. In the HA UI go to "Configuration" -> "Integrations", select the PR Custom Component with title `Tesla` Component's `...` menu and reload. This will automatically download the latest files from the Pull Request
2. Restart Home Assistant.

## Uninstalling an Auto Generated Custom Component

> This uses Tesla as an example.

1. In the HA UI go to "Configuration" -> "Integrations", select the `Tesla` Component's `...` menu and delete. This will uninstall the configured `Tesla` custom component from the HA instance.
2. Select the PR Custom Component with title `Tesla` Component's `...` menu and delete. This will delete custom files and restore the default).
3. Restart Home Assistant.
4. Hard refresh your browser

<!---->

## Contributions are welcome!

If you want to contribute to this please read the [Contribution guidelines](CONTRIBUTING.md)

_Component built with [integration_blueprint][integration_blueprint]._

## Logo

The [logo](images/pr_custom_component.svg) is a combination of the [Home Assistant logo](https://github.com/home-assistant/assets/blob/master/logo/logo.svg) available under [CC-BY-NC-SA-4.0](https://github.com/home-assistant/assets/blob/master/LICENSE.md) and the [Pull request icon](https://commons.wikimedia.org/wiki/File:Octicons-git-pull-request.svg) under [MIT](https://github.com/primer/octicons/blob/master/LICENSE). The combined logo is under [CC-BY-NC-SA-4.0](https://github.com/home-assistant/assets/blob/master/LICENSE.md)

---

[integration_blueprint]: https://github.com/custom-components/integration_blueprint
[buymecoffee]: https://www.buymeacoffee.com/alandtse
[buymecoffeebadge]: https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg?style=for-the-badge
[commits-shield]: https://img.shields.io/github/commit-activity/w/alandtse/pr_custom_component?style=for-the-badge
[commits]: https://github.com/alandtse/pr_custom_component/commits/main
[hacs]: https://github.com/custom-components/hacs
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge
[discord]: https://discord.gg/Qa5fW2R
[discord-shield]: https://img.shields.io/discord/330944238910963714.svg?style=for-the-badge
[forum-shield]: https://img.shields.io/badge/community-forum-brightgreen.svg?style=for-the-badge
[forum]: https://community.home-assistant.io/
[license]: LICENSE
[license-shield]: https://img.shields.io/github/license/alandtse/pr_custom_component.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-Alan%20Tse%20%40alandtse-blue.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/alandtse/pr_custom_component.svg?style=for-the-badge
[releases]: https://github.com/alandtse/pr_custom_component/releases
[download-all]: https://img.shields.io/github/downloads/alandtse/pr_custom_component/total?style=for-the-badge
[download-latest]: https://img.shields.io/github/downloads/alandtse/pr_custom_component/latest/total?style=for-the-badge
