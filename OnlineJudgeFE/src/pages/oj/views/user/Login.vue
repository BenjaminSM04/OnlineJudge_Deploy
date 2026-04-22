<template>
  <div class="auth-form">
    <Form ref="formLogin" :model="formLogin" :rules="ruleLogin">
      <FormItem prop="username">
        <Input type="text" v-model="formLogin.username" :placeholder="$t('m.LoginUsername')" size="large" @on-enter="handleLogin">
        <Icon type="ios-person-outline" slot="prepend"></Icon>
        </Input>
      </FormItem>
      <FormItem prop="password">
        <Input type="password" v-model="formLogin.password" :placeholder="$t('m.LoginPassword')" size="large" @on-enter="handleLogin">
        <Icon type="ios-locked-outline" slot="prepend"></Icon>
        </Input>
      </FormItem>
      <FormItem prop="tfa_code" v-if="tfaRequired">
        <Input v-model="formLogin.tfa_code" :placeholder="$t('m.TFA_Code')">
        <Icon type="ios-lightbulb-outline" slot="prepend"></Icon>
        </Input>
      </FormItem>
    </Form>
    <div class="footer">
      <Button
        type="primary"
        @click="handleLogin"
        class="btn auth-submit-btn" long
        :loading="btnLoginLoading">
        {{$t('m.UserLogin')}}
      </Button>
      <div class="auth-links">
        <a class="auth-link" v-if="website.allow_register" @click.stop="handleBtnClick('register')">{{$t('m.No_Account')}}</a>
        <a class="auth-link" @click.stop="goResetPassword">{{$t('m.Forget_Password')}}</a>
      </div>
    </div>
  </div>
</template>

<script>
  import { mapGetters, mapActions } from 'vuex'
  import api from '@oj/api'
  import { FormMixin } from '@oj/components/mixins'

  export default {
    mixins: [FormMixin],
    data () {
      const CheckRequiredTFA = (rule, value, callback) => {
        if (value !== '') {
          api.tfaRequiredCheck(value).then(res => {
            this.tfaRequired = res.data.data.result
          })
        }
        callback()
      }

      return {
        tfaRequired: false,
        btnLoginLoading: false,
        formLogin: {
          username: '',
          password: '',
          tfa_code: ''
        },
        ruleLogin: {
          username: [
            {required: true, trigger: 'blur'},
            {validator: CheckRequiredTFA, trigger: 'blur'}
          ],
          password: [
            {required: true, trigger: 'change', min: 6, max: 20}
          ]
        }
      }
    },
    methods: {
      ...mapActions(['changeModalStatus', 'getProfile']),
      handleBtnClick (mode) {
        this.changeModalStatus({
          mode,
          visible: true
        })
      },
      handleLogin () {
        this.validateForm('formLogin').then(valid => {
          this.btnLoginLoading = true
          let formData = Object.assign({}, this.formLogin)
          if (!this.tfaRequired) {
            delete formData['tfa_code']
          }
          api.login(formData).then(res => {
            this.btnLoginLoading = false
            this.changeModalStatus({visible: false})
            this.getProfile()
            this.$success(this.$i18n.t('m.Welcome_back'))
          }, _ => {
            this.btnLoginLoading = false
          })
        })
      },
      goResetPassword () {
        this.changeModalStatus({visible: false})
        this.$router.push({name: 'apply-reset-password'})
      }
    },
    computed: {
      ...mapGetters(['website', 'modalStatus']),
      visible: {
        get () {
          return this.modalStatus.visible
        },
        set (value) {
          this.changeModalStatus({visible: value})
        }
      }
    }
  }
</script>

<style scoped lang="less">
  @import (reference) '../../../../styles/theme-oj.less';

  .auth-form {
    /deep/ .ivu-form-item {
      margin-bottom: 18px;
    }

    /deep/ .ivu-input-group-prepend {
      background: #fff;
      border: 2px solid @oj-secondary;
      border-right: none;
      color: @oj-secondary;
      border-radius: 12px 0 0 12px;
      min-width: 46px;
    }

    /deep/ .ivu-input-group-prepend i {
      font-size: 20px;
      font-weight: 600;
    }

    /deep/ .ivu-input-group-prepend + .ivu-input {
      border: 2px solid @oj-secondary;
      border-left: none;
      border-radius: 0 12px 12px 0;
      height: 46px;
      font-size: 16px;
      padding-left: 12px;
      color: @oj-text;
    }

    /deep/ .ivu-input-group-prepend + .ivu-input:focus {
      box-shadow: 0 0 0 3px fade(@oj-primary, 18%);
    }

    /deep/ .ivu-input::placeholder {
      color: fade(@oj-secondary, 50%);
    }
  }

  .footer {
    overflow: auto;
    margin-top: 4px;
    text-align: left;

    .btn {
      margin: 0 0 14px 0;
      &:last-child {
        margin: 0;
      }
    }
  }

  .auth-submit-btn {
    height: 52px;
    border-radius: 8px;
    font-size: 18px;
    font-weight: 700;
    letter-spacing: 0.2px;
    background-color: @oj-secondary;
    border-color: @oj-secondary;
  }

  .auth-submit-btn:hover {
    background-color: @oj-primary;
    border-color: @oj-primary;
  }

  .auth-links {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 8px;
  }

  .auth-link {
    color: #202020;
    font-size: 16px;
    line-height: 1.2;
  }

  .auth-link:hover {
    color: @oj-primary;
  }
</style>
