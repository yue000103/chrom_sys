<template>
  <div class="system-config">
    <h2>系统配置</h2>
    <el-form label-width="120px">
      <el-form-item label="MQTT服务器">
        <el-input v-model="config.mqttHost" placeholder="broker.emqx.io" />
      </el-form-item>
      <el-form-item label="MQTT端口">
        <el-input v-model="config.mqttPort" placeholder="1883" />
      </el-form-item>
      <el-form-item label="数据采集间隔">
        <el-input v-model="config.dataInterval" placeholder="1000" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="saveConfig">保存配置</el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<script>
import { ref } from 'vue'

export default {
  name: 'SystemConfig',
  setup() {
    const config = ref({
      mqttHost: 'broker.emqx.io',
      mqttPort: '1883',
      dataInterval: '1000'
    })

    const saveConfig = () => {
      console.log('保存配置:', config.value)
    }

    return {
      config,
      saveConfig
    }
  }
}
</script>