
pic = mutagen.flac.Picture()
pic.data = image.data
pic.type = (image.type_index or 3)
pic.mime = image.mime_type
pic.desc = (image.desc or u'')
