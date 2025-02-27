/*
 * This source file is part of an OSTIS project. For the latest info, see http://ostis.net
 * Distributed under the MIT License
 * (See accompanying file COPYING.MIT or copy at http://opensource.org/licenses/MIT)
 */

#ifndef _sc_keynodes_h_
#define _sc_keynodes_h_

#include "sc-core/sc_helper.h"
#include "sc-core/sc_memory.h"

#include "sc_common_types.h"

_SC_KPM_EXTERN sc_result sc_common_resolve_keynode(
    sc_memory_context * ctx,
    char const * sys_idtf,
    sc_addr * keynode,
    sc_addr const init_memory_generated_structure);

#define RESOLVE_KEYNODE(ctx, keynode, init_memory_generated_structure) \
  if (sc_common_resolve_keynode(ctx, keynode##_str, &keynode, init_memory_generated_structure) != SC_RESULT_OK) \
  return SC_RESULT_ERROR

#endif
