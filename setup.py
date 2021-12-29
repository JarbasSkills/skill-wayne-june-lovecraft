#!/usr/bin/env python3
from setuptools import setup

# skill_id=package_name:SkillClass
PLUGIN_ENTRY_POINT = 'skill-wayne-june-lovecraft.jarbasai=skill_wayne_june_lovecraft:WayneJuneLovecraftReadingsSkill'

setup(
    # this is the package name that goes on pip
    name='ovos-skill-wayne-june-lovecraft',
    version='0.0.1',
    description='ovos wayne june lovecraft readings skill plugin',
    url='https://github.com/JarbasSkills/skill-public-domain-cartoons',
    author='JarbasAi',
    author_email='jarbasai@mailfence.com',
    license='Apache-2.0',
    package_dir={"skill_wayne_june_lovecraft": ""},
    package_data={'skill_wayne_june_lovecraft': ['locale/*', 'res/*', 'ui/*']},
    packages=['skill_wayne_june_lovecraft'],
    include_package_data=True,
    install_requires=["ovos_workshop~=0.0.5a1"],
    keywords='ovos skill plugin',
    entry_points={'ovos.plugin.skill': PLUGIN_ENTRY_POINT}
)
