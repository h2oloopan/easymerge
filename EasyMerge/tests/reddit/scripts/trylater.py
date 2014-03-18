# The contents of this file are subject to the Common Public Attribution
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
# The Original Code is reddit.
#
# The Original Developer is the Initial Developer.  The Initial Developer of
# the Original Code is reddit Inc.
#
# All portions of the code written by reddit are Copyright (c) 2006-2014 reddit
# Inc. All Rights Reserved.
###############################################################################

from pylons import g

from r2.lib import amqp
from r2.lib.hooks import all_hooks, get_hook
from r2.models.trylater import TryLater

PREFIX = "trylater."


def register_core_hooks():
    # any trylater hooks implemented in r2 should be registered in this
    # function to ensure that they are available when trylater runs.
    from r2.models.account import trylater_hooks
    trylater_hooks.register_all()


## Entry point
def run_trylater():
    register_core_hooks()

    our_hooks = (key[len(PREFIX):] for key in all_hooks().keys()
                 if key.startswith(PREFIX))
    with TryLater.multi_handle(our_hooks) as handleable:
        for system, mature_items in handleable.iteritems():
            hook_name = "trylater.%s" % system
            g.log.info("Trying %s", system)

            get_hook(hook_name).call(mature_items=mature_items)

    amqp.worker.join()
