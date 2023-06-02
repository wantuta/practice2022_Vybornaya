import ontology
import player
import xml.etree.ElementTree as ET
import asyncio

input = ET.parse('example.xml')
world = ontology.World.fromxml(input.getroot())

async def main():
    await asyncio.gather(*world.runnable())

asyncio.run(main())
