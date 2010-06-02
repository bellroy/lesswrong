#!/bin/bash

# "The contents of this file are subject to the Common Public Attribution
# License Version 1.0. (the "License"); you may not use this file except in
# compliance with the License. You may obtain a copy of the License at
# http://code.reddit.com/LICENSE. The License is based on the Mozilla Public
# License Version 1.1, but Sections 14 and 15 have been added to cover use of
# software over a computer network and provide for limited attribution for the
# Original Developer. In addition, Exhibit A has been modified to be consistent
# with Exhibit B.
# 
# Software distributed under the License is distributed on an "AS IS" basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License for
# the specific language governing rights and limitations under the License.
# 
# The Original Code is Reddit.
# 
# The Original Developer is the Initial Developer.  The Initial Developer of the
# Original Code is CondeNet, Inc.
# 
# All portions of the code written by CondeNet are Copyright (c) 2006-2008
# CondeNet, Inc. All Rights Reserved.
################################################################################

BASE_DIR=${1:-/srv/www/lesswrong.org/shared/files}
WIKI_DUMP_FILE="wiki.lesswrong.xml"
WIKI_DUMP_PATH="$BASE_DIR/$WIKI_DUMP_FILE"

# Download to a temp file
wget -q "http://wiki.lesswrong.com/$WIKI_DUMP_FILE.gz" -O "/tmp/$WIKI_DUMP_FILE.gz"

# Remove existing target file if present other wise gunzip won't extract
rm -f "/tmp/$WIKI_DUMP_FILE"

# Unzip
gunzip "/tmp/$WIKI_DUMP_FILE.gz"

# Move into place atomically (assuming on the same filesystem)
mv "/tmp/$WIKI_DUMP_FILE" "$WIKI_DUMP_PATH"
