<template>
  <div class="chromatography-process">
    <h2>液相色谱仪流程控制</h2>
    <ProcessSteps />
    <MethodEditor />
    <SampleQueue />
  </div>
</template>

<script>
import ProcessSteps from '../components/workflow/ProcessSteps.vue'
import MethodEditor from '../components/workflow/MethodEditor.vue'
import SampleQueue from '../components/workflow/SampleQueue.vue'

export default {
  name: 'ChromatographyProcess',
  components: {
    ProcessSteps,
    MethodEditor,
    SampleQueue
  }
}
</script>