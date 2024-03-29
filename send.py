from messageClient import lineNotify
from messageClient import discordWebhook
import config

import logging
logger = logging.getLogger(__name__)

def send(text, image=None, emergency=False):
    # LineNotifyで送信
    try:
        if config.lineTokens['general']:
            if image:
                image.seek(0)
            logger.debug('send to LineNotify(general)')
            lineNotify.send(config.lineTokens['general'], text, image)
        if emergency:
            if image:
                image.seek(0)
            if config.lineTokens['emergency']:
                logger.debug('send to LineNotify(emergency)')
                lineNotify.send(config.lineTokens['emergency'], text, image)
    except lineNotify.LineNotifyError as e:
        logger.warn(e)
    
    # Discordで送信
    try:
        if config.discordWebhookUrls['general']:
            if image:
                image.seek(0)
            logger.debug('send to discord(general)')
            discordWebhook.send(config.discordWebhookUrls['general'], text, image, imageExt='png')
        if emergency:
            if image:
                image.seek(0)
            if config.discordWebhookUrls['emergency']:
                logger.debug('send to discord(emergency)')
                discordWebhook.send(config.discordWebhookUrls['emergency'], text, image, imageExt='png')
    except discordWebhook.DiscordWebhookError as e:
        logger.warn(e)