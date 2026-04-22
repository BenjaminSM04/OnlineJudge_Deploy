<template>
  <div id="header">
    <Menu theme="light" mode="horizontal" @on-select="handleRoute" :active-name="activeMenu" class="oj-menu">
      <div class="logo"><span>{{website.website_name}}</span></div>
      <Menu-item name="/">
        <Icon type="home"></Icon>
        {{$t('m.Home')}}
      </Menu-item>
      <Menu-item name="/problem">
        <Icon type="ios-keypad"></Icon>
        {{$t('m.NavProblems')}}
      </Menu-item>
      <Menu-item name="/contest">
        <Icon type="trophy"></Icon>
        {{$t('m.Contests')}}
      </Menu-item>
      <Menu-item name="/status">
        <Icon type="ios-pulse-strong"></Icon>
        {{$t('m.NavStatus')}}
      </Menu-item>
      <Submenu name="rank">
        <template slot="title">
          <Icon type="podium"></Icon>
          {{$t('m.Rank')}}
        </template>
        <Menu-item name="/acm-rank">
          {{$t('m.ACM_Rank')}}
        </Menu-item>
        <Menu-item name="/oi-rank">
          {{$t('m.OI_Rank')}}
        </Menu-item>
      </Submenu>
      <Submenu name="about">
        <template slot="title">
          <Icon type="information-circled"></Icon>
          {{$t('m.About')}}
        </template>
        <Menu-item name="/about">
          {{$t('m.Judger')}}
        </Menu-item>
        <Menu-item name="/faq">
          {{$t('m.FAQ')}}
        </Menu-item>
      </Submenu>
      <div class="right-menu">
        <!-- Language Switcher -->
        <Dropdown class="drop-menu" @on-click="handleLanguageChange" placement="bottom" trigger="click">
          <Button type="text" class="drop-menu-title">
            <Icon type="earth"></Icon>
            <span>{{ currentLanguage }}</span>
            <Icon type="arrow-down-b"></Icon>
          </Button>
          <Dropdown-menu slot="list">
            <Dropdown-item name="es-LA">Español (LA)</Dropdown-item>
            <Dropdown-item name="en-US">English</Dropdown-item>
            <Dropdown-item name="zh-CN">简体中文</Dropdown-item>
            <Dropdown-item name="zh-TW">繁體中文</Dropdown-item>
          </Dropdown-menu>
        </Dropdown>

        <template v-if="!isAuthenticated">
          <div class="btn-menu">
            <Button type="primary"
                    ref="loginBtn"
                    class="nav-btn"
                    @click="handleBtnClick('login')">{{$t('m.Login')}}
            </Button>
            <Button v-if="website.allow_register"
                    type="primary"
                    class="nav-btn"
                    @click="handleBtnClick('register')">{{$t('m.Register')}}
            </Button>
          </div>
        </template>
        <template v-else>
          <Dropdown class="drop-menu" @on-click="handleRoute" placement="bottom" trigger="click">
            <Button type="text" class="drop-menu-title">{{ user.username }}
              <Icon type="arrow-down-b"></Icon>
            </Button>
            <Dropdown-menu slot="list">
              <Dropdown-item name="/user-home">{{$t('m.MyHome')}}</Dropdown-item>
              <Dropdown-item name="/status?myself=1">{{$t('m.MySubmissions')}}</Dropdown-item>
              <Dropdown-item name="/setting/profile">{{$t('m.Settings')}}</Dropdown-item>
              <Dropdown-item v-if="isAdminRole" name="/admin">{{$t('m.Management')}}</Dropdown-item>
              <Dropdown-item divided name="/logout">{{$t('m.Logout')}}</Dropdown-item>
            </Dropdown-menu>
          </Dropdown>
        </template>
      </div>
    </Menu>
    <Modal v-model="modalVisible" :width="560" class-name="auth-modal">
      <div slot="header" class="modal-title">{{$t('m.Welcome_to')}} {{website.website_name_shortcut || 'Lizard'}}</div>
      <component :is="modalStatus.mode" v-if="modalVisible"></component>
      <div slot="footer" style="display: none"></div>
    </Modal>
  </div>
</template>

<script>
  import { mapGetters, mapActions } from 'vuex'
  import login from '@oj/views/user/Login'
  import register from '@oj/views/user/Register'

  export default {
    components: {
      login,
      register
    },
    mounted () {
      this.getProfile()
    },
    methods: {
      ...mapActions(['getProfile', 'changeModalStatus']),
      handleRoute (route) {
        if (route && route.indexOf('admin') < 0) {
          this.$router.push(route)
        } else {
          window.open('/admin/')
        }
      },
      handleBtnClick (mode) {
        this.changeModalStatus({
          visible: true,
          mode: mode
        })
      },
      handleLanguageChange (lang) {
        this.$i18n.locale = lang
      }
    },
    computed: {
      ...mapGetters(['website', 'modalStatus', 'user', 'isAuthenticated', 'isAdminRole']),
      // 跟随路由变化
      activeMenu () {
        return '/' + this.$route.path.split('/')[1]
      },
      currentLanguage () {
        return this.$i18n.locale === 'es-LA' ? 'Español'
          : this.$i18n.locale === 'en-US' ? 'English'
          : this.$i18n.locale === 'zh-CN' ? '中文'
          : '繁體'
      },
      modalVisible: {
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

<style lang="less" scoped>
  @import (reference) '../../../styles/theme-oj.less';

  #header {
    min-width: 300px;
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    z-index: 1000;
    background-color: @oj-primary;
    box-shadow: 0 2px 10px 0 fade(#000, 22%);
    
    .oj-menu {
      background: @oj-primary;
      border-bottom: none;
      height: 70px;
      line-height: 70px;
    }
    
    /* Navbar theme */
    /deep/ .ivu-menu-light.ivu-menu-horizontal .ivu-menu-item, 
    /deep/ .ivu-menu-light.ivu-menu-horizontal .ivu-menu-submenu {
      color: #ffffff;
      font-weight: 600;
      font-size: 15px;
      height: 70px;
      line-height: 70px;
    }
    
    /deep/ .ivu-menu-light.ivu-menu-horizontal .ivu-menu-item-active, 
    /deep/ .ivu-menu-light.ivu-menu-horizontal .ivu-menu-item:hover, 
    /deep/ .ivu-menu-light.ivu-menu-horizontal .ivu-menu-submenu-active, 
    /deep/ .ivu-menu-light.ivu-menu-horizontal .ivu-menu-submenu:hover {
      color: @oj-success;
      border-bottom: 3px solid @oj-success;
    }

    /* Dropdown list under Rank/About/User/Language */
    /deep/ .ivu-select-dropdown .ivu-menu-item {
      color: @oj-text;
      font-weight: 500;
      border-bottom: none !important;
    }

    /deep/ .ivu-select-dropdown .ivu-menu-item:hover {
      background-color: fade(@oj-success, 70%);
      color: @oj-dark;
    }

    .logo {
      margin-left: 2%;
      margin-right: 2%;
      font-size: 20px;
      float: left;
      line-height: 70px;
      color: #ffffff;
    }

    .right-menu {
      float: right;
      display: flex;
      align-items: center;
      height: 70px;
      margin-right: 24px;
    }
    
    .drop-menu {
      margin-right: 16px;
      &-title {
        font-size: 16px;
        color: #ffffff;
        display: inline-flex;
        align-items: center;
        gap: 6px;
        font-weight: 600;
      }
    }

    /deep/ .drop-menu-title.ivu-btn-text:hover,
    /deep/ .drop-menu-title.ivu-btn-text:focus {
      color: @oj-success;
    }
    
    .btn-menu {
      display: flex;
      align-items: center;
      gap: 10px;
      
      .nav-btn {
        min-width: 126px;
        height: 38px;
        padding: 0 20px;
        background-color: @oj-secondary;
        border-color: @oj-secondary;
        color: #ffffff;
        font-weight: 700;
        font-size: 13px;
        border-radius: 6px;
        
        &:hover {
          background-color: @oj-primary;
          border-color: @oj-primary;
        }
      }
    }
  }

  .modal {
    &-title {
      font-size: 36px;
      line-height: 1.15;
      color: #111;
      font-weight: 600;
    }
  }
</style>
