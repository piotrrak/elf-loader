#include "vdl-init.h"
#include "vdl-utils.h"
#include "vdl-log.h"
#include "vdl-context.h"
#include "vdl-file.h"
#include "vdl-list.h"


// the glibc elf loader passes all 3 arguments
// to the initialization functions and the libc initializer
// function makes use of these arguments to initialize
// __libc_argc, __libc_argv, and, __environ so, we do the
// same for compatibility purposes.
typedef void (*init_function) (int, char **, char **);

static void
call_init (struct VdlFile *file)
{
  VDL_LOG_FUNCTION ("file=%s", file->name);

  VDL_LOG_ASSERT (!file->init_called, "file has already been initialized");

  file->init_called = 1;

  if (file->is_executable)
    {
      // The constructors of the main executable are
      // run by the libc initialization code which has
      // been linked into the binary by the compiler.
      // If we run them here, they will be run twice which
      // is not good. So, we just return.
      return;
    }

  // Gather information from the .dynamic section
  unsigned long dt_init = vdl_file_get_dynamic_p (file, DT_INIT);
  unsigned long dt_init_array = vdl_file_get_dynamic_p (file, DT_INIT_ARRAY);
  unsigned long dt_init_arraysz = vdl_file_get_dynamic_v (file, DT_INIT_ARRAYSZ);
  // First, invoke the old-style DT_INIT function.
  // The address of the function to call is stored in
  // the DT_INIT tag, here: dt_init.
  if (dt_init != 0)
    {
      init_function init = (init_function) dt_init;
      init (file->context->argc, file->context->argv, file->context->envp);
    }

  // Then, invoke the newer DT_INIT_ARRAY functions.
  // The address of the functions to call is stored as
  // an array of pointers pointed to by DT_INIT_ARRAY
  if (dt_init_array != 0)
    {
      init_function *init = (init_function *) dt_init_array;
      int i;
      for (i = 0; i < dt_init_arraysz / sizeof (init_function); i++, init++)
	{
	  (*(init[i])) (file->context->argc, file->context->argv, file->context->envp);
	}
    }

  vdl_context_notify (file->context, file, VDL_EVENT_CONSTRUCTED);
}

void vdl_init_call (struct VdlList *files)
{
  vdl_list_iterate (files, (void(*)(void*))call_init);
}