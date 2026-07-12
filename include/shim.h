#pragma once

#include <stdbool.h>
#include <stdint.h>
#include <sys/types.h>

#if defined(__linux__)
#include <re/re.h>

#include <baresip.h>
#elif defined(__APPLE__)
// On macOS with Homebrew, ensure libre's headers are included before
// baresip so types (e.g. enums/structs from libre) are defined.
#include </opt/homebrew/include/re/re.h>

#include </opt/homebrew/include/baresip.h>
#endif